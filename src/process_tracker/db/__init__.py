# src/process_tracker/db/__init__.py
from __future__ import annotations

from .session import Base, engine, AsyncSessionLocal, get_session  # re-export
from . import models  # noqa: F401  # регистрируем модели

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "init_db",
    "drop_db",
]

async def init_db() -> None:
    """Создать таблицы (для dev/тестов). В проде использовать Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db() -> None:
    """Удалить все таблицы (dev only!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
