from __future__ import annotations
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Role


class RoleRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get_by_name(self, name: str) -> Optional[Role]:
        res = await self.s.execute(select(Role).where(Role.name == name))
        return res.scalars().first()

    async def create(self, name: str, description: str | None = None) -> Role:
        obj = Role(name=name, description=description)
        self.s.add(obj)
        await self.s.flush()
        return obj
