# src/process_tracker/db/session.py
"""
Async SQLAlchemy:
- Единый путь к БД через settings.db_url_resolved (исключает «разные БД»)
- PRAGMA foreign_keys=ON для SQLite
- Ограничение параллелизма к БД (Semaphore)
- Глобальный таймаут на запросы задаётся в репозиториях (settings.db_query_timeout)
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from sqlalchemy import event
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings
from .models import Base  # noqa: F401  # важно импортнуть модели, чтобы metadata была общей

# --- URL и тип СУБД ----------------------------------------------------------
ENGINE_URL = settings.db_url_resolved
_url = make_url(ENGINE_URL)
_is_sqlite = _url.get_backend_name().startswith("sqlite")

# --- Настройки engine ---------------------------------------------------------
engine_kwargs: dict = dict(
    echo=settings.db_echo,
    future=True,
    pool_pre_ping=True,
)

# Для сетевых СУБД можно задать пул, если такие поля есть в настройках
if not _is_sqlite:
    if hasattr(settings, "db_pool_size"):
        engine_kwargs["pool_size"] = getattr(settings, "db_pool_size")
    if hasattr(settings, "db_max_overflow"):
        engine_kwargs["max_overflow"] = getattr(settings, "db_max_overflow")
    if hasattr(settings, "db_pool_recycle"):
        engine_kwargs["pool_recycle"] = getattr(settings, "db_pool_recycle")

engine = create_async_engine(ENGINE_URL, **engine_kwargs)

# Включаем внешние ключи для SQLite
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):  # pragma: no cover
    if _is_sqlite:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            # ничего страшного: просто оставим как есть
            pass

# --- Фабрика сессий -----------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Ограничение одновременных обращений к БД
DB_CONCURRENCY_SEM = asyncio.Semaphore(max(1, settings.db_max_concurrency))


async def get_session() -> AsyncIterator[AsyncSession]:
    """DI-совместимый провайдер сессии с ограничением конкурентности."""
    async with DB_CONCURRENCY_SEM:
        async with AsyncSessionLocal() as session:
            yield session
