from __future__ import annotations
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Permission, Role


class PermissionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get_by_name(self, name: str) -> Optional[Permission]:
        res = await self.s.execute(select(Permission).where(Permission.name == name))
        return res.scalars().first()

    async def create(self, name: str, description: str | None = None, dangerous: bool = False) -> Permission:
        obj = Permission(name=name, description=description, dangerous=dangerous)
        self.s.add(obj)
        await self.s.flush()
        return obj

    async def ensure(self, name: str, description: str | None = None, dangerous: bool = False) -> Permission:
        p = await self.get_by_name(name)
        if p:
            return p
        return await self.create(name, description, dangerous)

    async def grant(self, role: Role, perm: Permission) -> None:
        if perm not in role.permissions:
            role.permissions.append(perm)
            await self.s.flush()
