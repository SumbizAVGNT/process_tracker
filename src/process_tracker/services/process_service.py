# src/process_tracker/services/process_service.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from ..db.dal.process_repo import ProcessRepo

class ProcessService:
    def __init__(self, session: AsyncSession):
        self.repo = ProcessRepo(session)
        self.session = session

    async def get_recent(self):
        return await self.repo.list()

    async def create(self, title: str, description: str | None = None, status: str = "new"):
        item = await self.repo.create(title, description, status)
        await self.session.commit()
        return item
