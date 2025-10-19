from __future__ import annotations

import asyncio
from typing import AsyncIterator

from sqlalchemy import event
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings
from .models import Base  # noqa: F401  — чтобы metadata была загружена

ENGINE_URL = settings.db_url_resolved
_url = make_url(ENGINE_URL)
_is_sqlite = _url.get_backend_name().startswith("sqlite")

engine_kwargs: dict = dict(
    echo=settings.db_echo,
    future=True,
    pool_pre_ping=True,
)

# Для SQLite оставим дефолтный пул. Для других — настраиваем при наличии параметров.
if not _is_sqlite:
    if hasattr(settings, "db_pool_size"):
        engine_kwargs["pool_size"] = getattr(settings, "db_pool_size")
    if hasattr(settings, "db_max_overflow"):
        engine_kwargs["max_overflow"] = getattr(settings, "db_max_overflow")
    if hasattr(settings, "db_pool_recycle"):
        engine_kwargs["pool_recycle"] = getattr(settings, "db_pool_recycle")

engine = create_async_engine(ENGINE_URL, **engine_kwargs)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):  # pragma: no cover
    if _is_sqlite:
        try:
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
        except Exception:
            pass


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

DB_CONCURRENCY_SEM = asyncio.Semaphore(max(1, getattr(settings, "db_max_concurrency", 10)))


async def get_session() -> AsyncIterator[AsyncSession]:
    async with DB_CONCURRENCY_SEM:
        async with AsyncSessionLocal() as session:
            yield session
