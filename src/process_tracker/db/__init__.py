# src/process_tracker/db/__init__.py

from __future__ import annotations

from .session import Base, engine, AsyncSessionLocal, get_session  # re-export
from . import models  # noqa: F401  # регистрируем модели в metadata

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "init_db",
    "drop_db",
]


async def init_db() -> None:
    """
    Создать все таблицы на основе declarative Base.
    Использовать в dev/тестах; в prod — Alembic миграции.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Удалить все таблицы (Только для dev!).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
