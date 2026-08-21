from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _get_fernet() -> Fernet:
    if not settings.encryption_key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured."
        )

    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str) -> str:
    return _get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def decrypt_value(value: str) -> str:
    try:
        return _get_fernet().decrypt(
            value.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Unable to decrypt value."
        ) from exc
