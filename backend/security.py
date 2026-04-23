import os
import base64
import logging
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", "agent_room_stable_salt_v1")


def derive_key(passphrase: str, salt: str) -> bytes:
    """
    Menghasilkan kunci Fernet yang valid dan konsisten dari string apa pun.
    Salt diambil dari environment variable agar unik per-deployment.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key


# Inisialisasi Fernet secara aman
_fernet = None

if not SECRET_KEY:
    logger.critical(
        "⛔ SECRET_KEY tidak ditemukan di .env! "
        "Enkripsi/dekripsi API key TIDAK AKAN BERFUNGSI. "
        "Tambahkan SECRET_KEY ke file .env Anda."
    )
else:
    try:
        stable_key = derive_key(SECRET_KEY, ENCRYPTION_SALT)
        _fernet = Fernet(stable_key)
        logger.info("Sistem keamanan diinisialisasi dengan kunci stabil.")
    except Exception as e:
        logger.critical(f"⛔ Gagal menginisialisasi sistem keamanan: {e}")
        _fernet = None


def encrypt_api_key(api_key: str) -> str:
    """Enkripsi API key. Raise error jika sistem enkripsi tidak tersedia."""
    if not api_key:
        return ""
    if _fernet is None:
        raise RuntimeError(
            "Sistem enkripsi tidak tersedia. Pastikan SECRET_KEY sudah diset di .env"
        )
    try:
        return _fernet.encrypt(api_key.encode()).decode()
    except Exception as e:
        logger.error(f"Gagal mengenkripsi API Key: {e}")
        raise RuntimeError(f"Gagal mengenkripsi API Key: {e}")


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Dekripsi API key.
    Returns:
        - String API key jika berhasil
        - "" jika encrypted_key kosong
        - None jika dekripsi gagal (kunci berubah/korup)
    """
    if not encrypted_key:
        return ""
    if _fernet is None:
        logger.error("Dekripsi gagal: sistem enkripsi tidak tersedia (SECRET_KEY tidak diset).")
        return None
    try:
        return _fernet.decrypt(encrypted_key.encode()).decode()
    except InvalidToken:
        logger.error(
            "⛔ Dekripsi gagal: SECRET_KEY kemungkinan sudah berubah sejak API key ini disimpan. "
            "Data terenkripsi tidak dapat dipulihkan dengan kunci saat ini."
        )
        return None
    except Exception as e:
        logger.error(f"⛔ Dekripsi gagal dengan error tidak terduga: {e}")
        return None
