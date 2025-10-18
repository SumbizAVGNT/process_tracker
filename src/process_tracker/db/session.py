# src/process_tracker/db/session.py
"""
Async SQLAlchemy:
- Безопасные настройки пула (для не-SQLite)
- PRAGMA foreign_keys=ON для SQLite
- Ограничение параллелизма к БД (Semaphore)
- Глобальный таймаут на запросы (используется репозиториями)
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.engine.url import make_url

from ..core.config import settings

Base = declarative_base()

# Разбор URL — чтобы отличать sqlite от прочих
_url = make_url(settings.db_url)
_is_sqlite = _url.get_backend_name().startswith("sqlite")

engine_kwargs = dict(
    echo=False,
    future=True,
    pool_pre_ping=True,
)

if not _is_sqlite:
    # Для сетевых СУБД настраиваем пул
    engine_kwargs.update(
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
    )

engine = create_async_engine(settings.db_url, **engine_kwargs)

# Включаем внешние ключи для SQLite
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    if _is_sqlite:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Глобальный семафор для ограничения одновременных запросов к БД
DB_CONCURRENCY_SEM = asyncio.Semaphore(settings.db_max_concurrency)

async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
