import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

try:
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        fallback_key = Fernet.generate_key().decode()
        print(f"WARNING: SECRET_KEY not configured or invalid. Consider adding this to your .env: SECRET_KEY={fallback_key}")
        fernet = Fernet(fallback_key.encode())
    else:
        fernet = Fernet(SECRET_KEY.encode())
except Exception:
    fernet = Fernet(Fernet.generate_key())

def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    return fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    if not encrypted_key:
        return ""
    try:
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""
