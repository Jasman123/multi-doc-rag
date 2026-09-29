from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import get_settings


@lru_cache
def _get_fernet() -> Fernet:
    return Fernet(get_settings().encryption_key.encode())

def encrypt_secret(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()

def decrypt_secret(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()