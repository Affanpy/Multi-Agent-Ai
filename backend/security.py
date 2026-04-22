import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

# Setup logging untuk profesionalitas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

def derive_key(passphrase: str) -> bytes:
    """
    Menghasilkan kunci Fernet yang valid dan konsisten dari string apa pun.
    Ini memastikan enkripsi tetap stabil meskipun server di-restart.
    """
    # Gunakan salt statis agar hasil derivasi selalu sama untuk passphrase yang sama.
    salt = b'agent_room_stable_salt_v1' 
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key

# Inisialisasi Fernet secara aman
try:
    if not SECRET_KEY:
        logger.warning("SECRET_KEY tidak ditemukan di .env! Menggunakan kunci sementara (TIDAK AMAN UNTUK PRODUKSI).")
        # Gunakan passphrase default yang stabil agar data tidak rusak saat dev
        SECRET_KEY = "fallback_temporary_secret_for_development_only"
    
    stable_key = derive_key(SECRET_KEY)
    fernet = Fernet(stable_key)
    logger.info("Sistem keamanan diinisialisasi dengan kunci stabil.")
except Exception as e:
    logger.error(f"Gagal menginisialisasi sistem keamanan: {e}")
    # Fallback terakhir jika semua gagal
    fernet = Fernet(Fernet.generate_key())

def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    try:
        return fernet.encrypt(api_key.encode()).decode()
    except Exception as e:
        logger.error(f"Gagal mengenkripsi API Key: {e}")
        return ""

def decrypt_api_key(encrypted_key: str) -> str:
    if not encrypted_key:
        return ""
    try:
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Gagal mendekripsi API Key. Kemungkinan SECRET_KEY berubah atau data korup.")
        return ""
