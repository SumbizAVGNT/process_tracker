# src/process_tracker/db/dal/base.py
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from ..session import DB_CONCURRENCY_SEM
from ...core.config import settings

T = TypeVar("T")

class BaseRepo:
    """
    Базовый репозиторий:
    - Все операции оборачивает в asyncio.wait_for с таймаутом settings.db_query_timeout
    - Ограничивает параллельные обращения к БД через глобальный семафор DB_CONCURRENCY_SEM
    - Не допускает raw SQL-конкатенаций: используем только SQLAlchemy Core/ORM
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    @asynccontextmanager
    async def _guard(self) -> AsyncIterator[None]:
        async with DB_CONCURRENCY_SEM:
            yield

    async def _with_timeout(self, func: Callable[[], T]) -> T:
        return await asyncio.wait_for(asyncio.to_thread(func), timeout=settings.db_query_timeout)

    async def _await_timeout(self, coro):
        return await asyncio.wait_for(coro, timeout=settings.db_query_timeout)
