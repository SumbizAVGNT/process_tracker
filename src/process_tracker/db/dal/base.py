from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, TypeVar, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from ..session import DB_CONCURRENCY_SEM
from ...core.config import settings

T = TypeVar("T")


class BaseRepo:
    """
    Базовый репозиторий:
    - ограничивает параллельные обращения к БД через глобальный семафор DB_CONCURRENCY_SEM
    - оборачивает операции в asyncio.wait_for с таймаутом settings.db_query_timeout
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._timeout = getattr(settings, "db_query_timeout", 30.0)

    @asynccontextmanager
    async def _guard(self) -> AsyncIterator[None]:
        async with DB_CONCURRENCY_SEM:
            yield

    async def _with_timeout(self, func: Callable[[], T]) -> T:
        return await asyncio.wait_for(asyncio.to_thread(func), timeout=self._timeout)

    async def _await_timeout(self, coro: Awaitable[T]) -> T:
        return await asyncio.wait_for(coro, timeout=self._timeout)
