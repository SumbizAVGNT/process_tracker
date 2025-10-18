# src/process_tracker/core/security.py
from __future__ import annotations

from typing import Optional

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from .config import settings

# Используем bcrypt_sha256 как основной, bcrypt — для совместимости старых хэшей.
_pwd = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Хэш пароля с солью.
    bcrypt_sha256 снимает ограничение 72 байта (Passlib делает предварительный SHA-256).
    """
    return _pwd.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Проверка пароля. Поддерживает как bcrypt_sha256, так и legacy bcrypt.
    """
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
