from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Role, Permission


class RoleRepo(BaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_code(self, code: str) -> Optional[Role]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(Role).where(Role.code == code)))
            return res.scalars().first()

    async def create(self, code: str, title: str | None = None, description: str | None = None) -> Role:
        async with self._guard():
            obj = Role(code=code, title=title or code.title(), description=description)
            self.session.add(obj)
            await self._await_timeout(self.session.flush())
            return obj

    async def ensure(self, code: str, title: str | None = None, description: str | None = None) -> Role:
        role = await self.get_by_code(code)
        if role:
            return role
        return await self.create(code=code, title=title, description=description)

    async def grant(self, role: Role, perm: Permission) -> None:
        async with self._guard():
            if perm not in role.permissions:
                role.permissions.append(perm)
                await self._await_timeout(self.session.flush())
