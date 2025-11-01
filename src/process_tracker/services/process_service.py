from __future__ import annotations

from typing import List, Optional, Callable, AsyncIterator

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..db.models import Process


class ProcessService:
    """
    Сервис процессов с мягкой зависимостью от сессии:
    - можно передать уже открытую AsyncSession
    - можно создать без аргументов — он сам откроет AsyncSessionLocal()
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        session_factory: Optional[Callable[[], AsyncIterator[AsyncSession]]] = None,
    ) -> None:
        self._session: Optional[AsyncSession] = session
        self._session_factory = session_factory  # не обязателен

    # ---- Вспомогательный контекст ----

    async def _open_session(self) -> AsyncIterator[AsyncSession]:
        if self._session is not None:
            # уже есть внешняя сессия — просто отдаём её
            yield self._session
            return

        if self._session_factory is not None:
            # пользователь дал фабрику (async generator)
            async for s in self._session_factory():
                yield s
            return

        # по умолчанию — свой AsyncSessionLocal
        async with AsyncSessionLocal() as s:
            yield s

    # ---- Операции ----

    async def create(self, name: str, description: Optional[str], status: str = "new") -> Process:
        """
        NB: модель Process имеет поле `name`, а не `title`.
        """
        async for s in self._open_session():
            obj = Process(name=name, description=description, status=status)
            s.add(obj)
            await s.flush()
            await s.commit()
            await s.refresh(obj)
            return obj
        raise RuntimeError("No session available")

    async def list_recent(self, *, limit: int = 50) -> List[Process]:
        async for s in self._open_session():
            # TimestampMixin: есть created_at/updated_at — используем updated_at если доступен
            order_col = getattr(Process, "updated_at", None) or getattr(Process, "created_at", None)
            res = await s.scalars(
                select(Process)
                .order_by(desc(order_col))
                .limit(limit)
            )
            return list(res)
        return []

    async def get_recent(self, *, limit: int = 50) -> List[Process]:
        return await self.list_recent(limit=limit)
