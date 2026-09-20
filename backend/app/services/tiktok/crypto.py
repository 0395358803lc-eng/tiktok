from cryptography.fernet import Fernet

from app.core.settings import get_settings


def _fernet() -> Fernet:
    key = get_settings().token_encryption_key.get_secret_value().encode("utf-8")
    return Fernet(key)


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: str) -> str:
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
