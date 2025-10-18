from __future__ import annotations

from typing import Optional

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from .config import settings

# Современный и стабильный алгоритм, не зависит от bcrypt
_pwd = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=310_000,  # близко к рекомендациям OWASP
)


def hash_password(password: str) -> str:
    """Хэш пароля с солью (PBKDF2-SHA256)."""
    return _pwd.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверка пароля."""
    try:
        return _pwd.verify(plain_password, password_hash)
    except Exception:
        return False


# ---------- Симметричное шифрование полезных данных (токены и т.п.) ----------

_FERNET: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _FERNET
    if _FERNET is None:
        key = settings.crypt_fernet_key
        key_bytes = key.encode() if isinstance(key, str) else key
        _FERNET = Fernet(key_bytes)
    return _FERNET


def encrypt(text: str) -> str:
    return _get_fernet().encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
