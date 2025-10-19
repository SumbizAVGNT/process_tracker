from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Process


class ProcessRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, process_id: int) -> Optional[Process]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(Process).where(Process.id == process_id)))
            return res.scalars().first()

    async def list(self) -> list[Process]:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Process).order_by(Process.id.desc()))
            )
            return list(res.scalars().all())

    async def create(
        self,
        name: str,
        description: str | None = None,
        status: str = "active",
    ) -> Process:
        async with self._guard():
            item = Process(name=name, description=description, status=status)
            self.session.add(item)
            await self._await_timeout(self.session.flush())
            return item
