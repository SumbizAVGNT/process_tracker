# src/process_tracker/db/dal/process_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Process

class ProcessRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list(self) -> list[Process]:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Process).order_by(Process.id.desc()))
            )
            return list(res.scalars().all())

    async def create(self, title: str, description: str | None = None, status: str = "new") -> Process:
        async with self._guard():
            item = Process(title=title, description=description, status=status)
            self.session.add(item)
            await self._await_timeout(self.session.flush())
            return item
