# src/process_tracker/db/dal/permission_repo.py
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Permission, Role


class PermissionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------- CRUD ----------

    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.name == name)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def ensure_many(self, names: Iterable[str]) -> dict[str, Permission]:
        """Гарантирует наличие прав с этими именами, возвращает словарь name->Permission."""
        names = [n.strip().lower() for n in names if n and n.strip()]
        if not names:
            return {}
        stmt = select(Permission).where(Permission.name.in_(names))
        res = await self.session.execute(stmt)
        existing = {p.name: p for p in res.scalars().all()}

        for n in names:
            if n not in existing:
                p = Permission(name=n, description=f"Permission {n}")
                self.session.add(p)
                existing[n] = p
        await self.session.flush()
        return existing

    # ---------- Role <-> Permission ----------

    async def _ensure_role_permissions_loaded(self, role: Role) -> None:
        """
        Явно подгрузить role.permissions в async-режиме.
        Это предотвращает MissingGreenlet при неявной ленивой загрузке.
        """
        # если коллекция уже в __dict__ — значит загружена/инициализирована
        if "permissions" in role.__dict__:
            return
        await self.session.refresh(role, attribute_names=["permissions"])

    async def grant(self, role: Role, perm: Permission) -> bool:
        """
        Назначить право роли. Возвращает True, если право добавлено.
        """
        await self._ensure_role_permissions_loaded(role)
        if perm not in role.permissions:
            role.permissions.append(perm)
            await self.session.flush()
            return True
        return False

    async def revoke(self, role: Role, perm: Permission) -> bool:
        """
        Убрать право у роли. Возвращает True, если право было убрано.
        """
        await self._ensure_role_permissions_loaded(role)
        if perm in role.permissions:
            role.permissions.remove(perm)
            await self.session.flush()
            return True
        return False

    async def has(self, role: Role, perm: Permission) -> bool:
        """Проверить наличие права у роли (без неявной ленивой загрузки)."""
        await self._ensure_role_permissions_loaded(role)
        return perm in role.permissions
