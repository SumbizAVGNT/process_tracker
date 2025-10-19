from __future__ import annotations

from typing import Sequence, Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..db.models import Process


class ProcessService:
    """
    Сервис работы с процессами. Сам управляет жизненным циклом сессии,
    используя фабрику AsyncSessionLocal.
    """

    def __init__(self, session_factory=AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def count_all(self) -> int:
        async with self._session_factory() as session:  # type: AsyncSession
            res = await session.execute(select(func.count(Process.id)))
            return int(res.scalar_one())

    async def list_recent(self, limit: int = 50) -> Sequence[Process]:
        async with self._session_factory() as session:  # type: AsyncSession
            res = await session.execute(
                select(Process).order_by(desc(Process.created_at)).limit(max(1, limit))
            )
            return list(res.scalars().all())

    # совместимость, если где-то вызывали get_recent()
    async def get_recent(self, limit: int = 50) -> Sequence[Process]:
        return await self.list_recent(limit=limit)

    async def get(self, process_id: int) -> Optional[Process]:
        async with self._session_factory() as session:  # type: AsyncSession
            return await session.get(Process, process_id)

    async def create(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "new",
    ) -> Process:
        title = (title or "").strip()
        if not title:
            raise ValueError("title is required")

        async with self._session_factory() as session:  # type: AsyncSession
            obj = Process(title=title, description=description, status=status)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj


__all__ = ["ProcessService"]
