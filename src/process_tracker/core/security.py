# src/process_tracker/core/security.py
"""
Безопасность:
- Хэширование паролей (bcrypt) через passlib
- Симметричное шифрование/дешифрование (Fernet) через cryptography
Ключ Fernet берётся из settings.crypt_fernet_key.

⚠️ Ключ должен быть сгенерирован как:
>>> from cryptography.fernet import Fernet
>>> Fernet.generate_key().decode()
И записан в .env как CRYPT_FERNET_KEY=...
"""

from __future__ import annotations

from typing import Optional

from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken

from .config import settings

__all__ = [
    "hash_password",
    "verify_password",
    "get_fernet",
    "encrypt",
    "decrypt",
]

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Вернуть bcrypt-хэш пароля."""
    return _pwd.hash(password)


def verify_password(password: str, hash_: str) -> bool:
    """Проверить соответствие пароля и хэша."""
    return _pwd.verify(password, hash_)


def get_fernet() -> Fernet:
    """
    Вернуть инстанс Fernet, инициализированный ключом из настроек.
    Бросит ValueError, если ключ некорректный (не base64URL 32 байта).
    """
    try:
        return Fernet(settings.crypt_fernet_key.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise ValueError(
            "Неверный CRYPT_FERNET_KEY. Сгенерируй ключ через Fernet.generate_key().decode() и помести в .env"
        ) from e


def encrypt(plain_text: str) -> str:
    """
    Зашифровать строку в токен (base64url).
    """
    f = get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt(token: str, *, default: Optional[str] = "") -> Optional[str]:
    """
    Расшифровать токен.
    Возвращает default (по умолчанию пустую строку), если токен битый/истёк.
    """
    try:
        f = get_fernet()
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return default
