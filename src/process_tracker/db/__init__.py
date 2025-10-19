from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine, AsyncSessionLocal  # важно!
from .models import Base
from .migrations import upgrade_head_with_bootstrap
from .seed import seed_rbac

__all__ = ["init_db", "drop_db", "bootstrap_db"]


async def init_db() -> None:
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
            pass
        for table in Base.metadata.sorted_tables:
            try:
                await conn.run_sync(lambda sc, t=table: t.create(sc, checkfirst=True))
            except OperationalError:
                pass


async def drop_db() -> None:
    async with engine.begin() as conn:
        try:
            await conn.run_sync(lambda sc: Base.metadata.drop_all(sc))
        except OperationalError:
            pass


async def bootstrap_db() -> None:
    """
    Полный цикл:
      - Alembic bootstrap + upgrade head (автогенерируем «init», если нужно)
      - сид RBAC
    """
    # alembic — синхронный; гоняем в отдельном потоке
    import asyncio
    await asyncio.to_thread(upgrade_head_with_bootstrap)

    async with AsyncSessionLocal() as s:
        await seed_rbac(s)
