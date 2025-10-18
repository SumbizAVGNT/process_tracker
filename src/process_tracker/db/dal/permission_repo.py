# src/process_tracker/db/dal/permission_repo.py
from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Permission, Role


class PermissionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------- CRUD ----------

    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.name == name.strip().lower())
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def ensure(self, name: str, description: Optional[str] = None, dangerous: bool = False) -> Permission:
        """
        Гарантирует наличие права с именем `name`.
        Если существует — при необходимости обновит description/dangerous.
        Возвращает объект Permission.
        """
        n = name.strip().lower()
        stmt = select(Permission).where(Permission.name == n)
        res = await self.session.execute(stmt)
        perm = res.scalar_one_or_none()
        if perm is None:
            perm = Permission(name=n, description=description or f"Permission {n}")
            # поле dangerous может отсутствовать в модели — проверим аккуратно
            if hasattr(perm, "dangerous"):
                setattr(perm, "dangerous", bool(dangerous))
            self.session.add(perm)
            await self.session.flush()
            return perm

        updated = False
        if description and perm.description != description:
            perm.description = description
            updated = True
        if hasattr(perm, "dangerous"):
            cur = bool(getattr(perm, "dangerous"))
            if cur != bool(dangerous):
                setattr(perm, "dangerous", bool(dangerous))
                updated = True
        if updated:
            await self.session.flush()
        return perm

    async def ensure_many(
        self,
        items: Iterable[str] | Iterable[Tuple[str, Optional[str], bool]],
    ) -> dict[str, Permission]:
        """
        Удобный батч:
          - если передан список строк — создаст права с дефолтным описанием;
          - если переданы кортежи (name, description, dangerous).
        Возвращает {name -> Permission}.
        """
        result: dict[str, Permission] = {}
        normalized: list[Tuple[str, Optional[str], bool]] = []

        # нормализуем вход
        first = next(iter(items), None)  # type: ignore[arg-type]
        if first is None:
            return {}
        # вернём итератор назад
        it = items if isinstance(items, Sequence) else [first, *list(items)][0:]  # type: ignore[list-item]
        for x in it:  # type: ignore[assignment]
            if isinstance(x, tuple):
                n, d, dg = (x + (None, False))[0:3]  # безопасно добьём недостающие
                normalized.append((str(n).strip().lower(), d, bool(dg)))
            else:
                normalized.append((str(x).strip().lower(), None, False))

        # одним запросом забираем существующие
        names = [n for n, _, _ in normalized]
        if not names:
            return {}

        stmt = select(Permission).where(Permission.name.in_(names))
        res = await self.session.execute(stmt)
        existing = {p.name: p for p in res.scalars().all()}

        for n, d, dg in normalized:
            if n in existing:
                p = existing[n]
                # возможно, обновим поля
                updated = False
                if d and p.description != d:
                    p.description = d
                    updated = True
                if hasattr(p, "dangerous"):
                    cur = bool(getattr(p, "dangerous"))
                    if cur != bool(dg):
                        setattr(p, "dangerous", bool(dg))
                        updated = True
                if updated:
                    await self.session.flush()
                result[n] = p
            else:
                p = Permission(name=n, description=d or f"Permission {n}")
                if hasattr(p, "dangerous"):
                    setattr(p, "dangerous", bool(dg))
                self.session.add(p)
                await self.session.flush()
                result[n] = p

        return result

    # ---------- Role <-> Permission ----------

    async def _ensure_role_permissions_loaded(self, role: Role) -> None:
        """
        Явно подгружаем role.permissions, чтобы не ловить MissingGreenlet
        при ленивой загрузке в async-режиме.
        """
        if "permissions" not in role.__dict__:
            await self.session.refresh(role, attribute_names=["permissions"])

    async def grant(self, role: Role, perm: Permission) -> bool:
        """Назначить право роли. True — право добавлено."""
        await self._ensure_role_permissions_loaded(role)
        if perm not in role.permissions:
            role.permissions.append(perm)
            await self.session.flush()
            return True
        return False

    async def revoke(self, role: Role, perm: Permission) -> bool:
        """Убрать право у роли. True — право было убрано."""
        await self._ensure_role_permissions_loaded(role)
        if perm in role.permissions:
            role.permissions.remove(perm)
            await self.session.flush()
            return True
        return False

    async def has(self, role: Role, perm: Permission) -> bool:
        """Проверить наличие права у роли."""
        await self._ensure_role_permissions_loaded(role)
        return perm in role.permissions
