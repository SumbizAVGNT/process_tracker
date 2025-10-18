# src/process_tracker/db/dal/role_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Role

class RoleRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_name(self, name: str) -> Role | None:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Role).where(Role.name == name))
            )
            return res.scalars().first()

    async def create(self, name: str, description: str | None = None) -> Role:
        async with self._guard():
            role = Role(name=name, description=description)
            self.session.add(role)
            await self._await_timeout(self.session.flush())
            return role
