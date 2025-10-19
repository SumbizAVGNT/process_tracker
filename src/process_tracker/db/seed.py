from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Role, Permission


async def _get_or_create(
    session: AsyncSession,
    model,
    where: dict,
    defaults: dict | None = None,
):
    obj = (await session.execute(select(model).filter_by(**where))).scalars().first()
    if obj:
        return obj, False
    obj = model(**{**where, **(defaults or {})})
    session.add(obj)
    await session.flush()
    return obj, True


async def seed_rbac(session: AsyncSession) -> None:
    """
    Базовые роли/права для быстрого старта.
    """
    # Права
    perms = [
        ("tasks.read", "Чтение задач"),
        ("tasks.write", "Изменение задач"),
        ("processes.read", "Чтение процессов"),
        ("processes.write", "Изменение процессов"),
        ("templates.manage", "Управление шаблонами"),
        ("settings.read", "Чтение настроек"),
        ("settings.write", "Изменение настроек"),
        ("admin.*", "Полный доступ"),
    ]
    perm_objs: dict[str, Permission] = {}
    for code, title in perms:
        p, _ = await _get_or_create(session, Permission, {"code": code}, {"title": title})
        perm_objs[code] = p

    # Роли
    roles = {
        "admin": ["admin.*"],
        "manager": ["tasks.read", "tasks.write", "processes.read", "processes.write", "settings.read"],
        "user": ["tasks.read", "processes.read"],
    }
    for code, perm_codes in roles.items():
        role, _ = await _get_or_create(session, Role, {"code": code}, {"title": code.title()})
        role.permissions[:] = [perm_objs[c] for c in perm_codes if c in perm_objs]

    await session.commit()
