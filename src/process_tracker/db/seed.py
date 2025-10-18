# src/process_tracker/db/seed.py
"""
Начальное заполнение ролей и прав (RBAC).
Роли: admin, manager, user, viewer
Права:
- admin.*                           (опасное)
- process.read, process.write
- task.create, task.update, task.delete
- settings.read, settings.write
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .dal.role_repo import RoleRepo
from .dal.permission_repo import PermissionRepo

DEFAULT_ROLES = {
    "admin": "Полные права администратора",
    "manager": "Управление процессами и задачами",
    "user": "Базовые пользовательские права",
    "viewer": "Только просмотр",
}

DEFAULT_PERMS = [
    ("admin.*", "Все административные операции", True),
    ("process.read", "Чтение процессов", False),
    ("process.write", "Создание/редактирование процессов", False),
    ("task.create", "Создание задач", False),
    ("task.update", "Обновление задач", False),
    ("task.delete", "Удаление задач", False),
    ("settings.read", "Чтение настроек", False),
    ("settings.write", "Изменение настроек", True),
]

ROLE_MATRIX = {
    "admin": ["admin.*"],
    "manager": ["process.read", "process.write", "task.create", "task.update", "task.delete", "settings.read"],
    "user": ["process.read", "task.create", "task.update"],
    "viewer": ["process.read"],
}

async def seed_rbac(session: AsyncSession) -> None:
    rrepo = RoleRepo(session)
    prepo = PermissionRepo(session)

    # Ensure perms
    perms = {}
    for name, desc, dangerous in DEFAULT_PERMS:
        perms[name] = await prepo.ensure(name, desc, dangerous)

    # Ensure roles
    roles = {}
    for name, desc in DEFAULT_ROLES.items():
        role = await rrepo.get_by_name(name)
        if not role:
            role = await rrepo.create(name, desc)
        roles[name] = role

    # Grant
    for role_name, perm_names in ROLE_MATRIX.items():
        role = roles[role_name]
        for perm_name in perm_names:
            await prepo.grant(role, perms[perm_name])

    await session.commit()
