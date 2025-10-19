from __future__ import annotations

# Регистрация всех моделей в Base.metadata через побочный импорт
from .models import (  # noqa: F401
    Base,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    TaskType,
    Task,
    Process,
    FormDef,
)

__all__ = [
    "Base",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
    "TaskType",
    "Task",
    "Process",
    "FormDef",
]
