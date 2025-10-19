from __future__ import annotations
"""
DB package public API:
- init_db()      — идемпотентная инициализация схемы
- drop_db()      — дроп всех таблиц
- bootstrap_db() — миграции (если есть alembic) + сид RBAC
"""

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine, AsyncSessionLocal
from .models import Base               # регистрирует metadata
from . import models_meta as _models   # noqa: F401 — импортируем модели в metadata

__all__ = ["init_db", "drop_db", "bootstrap_db"]


async def init_db() -> None:
    """
    Идемпотентная инициализация схемы БД:
    - включает полезные PRAGMA для SQLite
    - создаёт недостающие таблицы (create_all)
    """
    async with engine.begin() as conn:
        if engine.url.get_backend_name().startswith("sqlite"):
            for pragma in ("foreign_keys=ON", "journal_mode=WAL", "synchronous=NORMAL"):
                try:
                    await conn.execute(text(f"PRAGMA {pragma}"))
                except Exception:
                    pass
        try:
            await conn.run_sync(lambda sc: Base.metadata.create_all(sc))
        except OperationalError:
            # например, при редком конфликте/гонке — не валим приложение
            pass


async def drop_db() -> None:
    async with engine.begin() as conn:
        try:
            await conn.run_sync(lambda sc: Base.metadata.drop_all(sc))
        except OperationalError:
            pass


async def bootstrap_db() -> None:
    """
    Полный bootstrap:
      1) Alembic upgrade head (если доступен и сконфигурирован)
      2) Сид базовых ролей/прав (RBAC)
    """
    import asyncio

    # 1) миграции (необязательно)
    try:
        from .migrations import upgrade_head_with_bootstrap
        await asyncio.to_thread(upgrade_head_with_bootstrap)
    except Exception:
        pass

    # 2) сид RBAC (необязателен для старта, но желателен)
    try:
        from .seed import seed_rbac
        async with AsyncSessionLocal() as s:
            await seed_rbac(s)
    except Exception:
        pass
