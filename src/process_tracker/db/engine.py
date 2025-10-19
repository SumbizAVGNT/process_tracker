from __future__ import annotations

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

from ..core.config import settings


def make_sync_url(db_url: str) -> str:
    """
    Конвертирует async URL → sync URL (для Alembic и прочих sync-инструментов).

    sqlite+aiosqlite://  -> sqlite://
    postgresql+asyncpg:// -> postgresql+psycopg:// (или другой sync-драйвер)
    """
    url = make_url(db_url)
    drivername = url.drivername

    if drivername.startswith("sqlite+aiosqlite"):
        url = url.set(drivername="sqlite")
    elif drivername.startswith("postgresql+asyncpg"):
        # подставляем современный sync-драйвер psycopg (psycopg3)
        url = url.set(drivername="postgresql+psycopg")

    return str(url)


def create_sync_engine() -> Engine:
    """
    Создаёт sync-движок (используется Alembic-ом).
    """
    sync_url = make_sync_url(settings.db_url_resolved)
    return _create_engine(sync_url, future=True, pool_pre_ping=True)
