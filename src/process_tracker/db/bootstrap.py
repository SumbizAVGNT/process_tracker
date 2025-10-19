from __future__ import annotations

import asyncio

from .migrations import upgrade_head_with_bootstrap
from .seed import seed_rbac
from .session import AsyncSessionLocal


def run_migrations_blocking() -> None:
    try:
        upgrade_head_with_bootstrap()
    except Exception:
        pass


async def run_seed() -> None:
    async with AsyncSessionLocal() as s:
        await seed_rbac(s)


def bootstrap_all_blocking() -> None:
    run_migrations_blocking()
    asyncio.run(run_seed())
