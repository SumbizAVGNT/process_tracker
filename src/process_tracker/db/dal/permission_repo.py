# src/process_tracker/db/dal/permission_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Permission, Role, RolePermission

class PermissionRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_name(self, name: str) -> Permission | None:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Permission).where(Permission.name == name))
            )
            return res.scalars().first()

    async def ensure(self, name: str, description: str = "", dangerous: bool = False) -> Permission:
        async with self._guard():
            existing = await self.get_by_name(name)
            if existing:
                return existing
            p = Permission(name=name, description=description, dangerous=dangerous)
            self.session.add(p)
            await self._await_timeout(self.session.flush())
            return p

    async def grant(self, role: Role, perm: Permission) -> None:
        """Назначить разрешение роли (idempotent)."""
        async with self._guard():
            # Проверка осуществляется через relationship, SQLAlchemy сам параметризует
            if perm not in role.permissions:
                role.permissions.append(perm)
                self.session.add(role)
                await self._await_timeout(self.session.flush())
