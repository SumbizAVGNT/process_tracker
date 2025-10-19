from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Permission


class PermissionRepo(BaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_code(self, code: str) -> Optional[Permission]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(Permission).where(Permission.code == code)))
            return res.scalars().first()

    async def create(self, code: str, title: str | None = None, description: str | None = None) -> Permission:
        async with self._guard():
            obj = Permission(code=code, title=title, description=description)
            self.session.add(obj)
            await self._await_timeout(self.session.flush())
            return obj

    async def ensure(self, code: str, title: str | None = None, description: str | None = None) -> Permission:
        perm = await self.get_by_code(code)
        if perm:
            return perm
        return await self.create(code=code, title=title, description=description)
