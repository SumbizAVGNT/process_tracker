# src/process_tracker/db/session.py
"""
Инициализация асинхронного SQLAlchemy:
- Async engine (URL из settings.db_url)
- async_sessionmaker
- get_session() — async dependency/generator
- Для SQLite включает PRAGMA foreign_keys=ON
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from ..core.config import settings

# Declarative base для моделей
Base = declarative_base()

# Async engine
engine = create_async_engine(
    settings.db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,  # безопаснее при долгих коннектах (не страшно и для sqlite)
)

# Включаем внешние ключи для SQLite (важно!)
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # На других СУБД просто тихо игнорируем
        pass

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Универсальный провайдер сессии (генератор)
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
