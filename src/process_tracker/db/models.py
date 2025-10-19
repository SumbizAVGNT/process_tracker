from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .types import JSON_AUTO as JSON

# ───────────────────────── Base / Mixins ─────────────────────────

class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


# ───────────────────────── RBAC ─────────────────────────
# Users, Roles, Permissions + association models:
#   - UserRole        (user_id, role_id)
#   - RolePermission  (role_id, permission_id)

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles", back_populates="users", lazy="selectin"
    )

    tasks_assigned: Mapped[List["Task"]] = relationship(
        back_populates="assignee", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)

    users: Mapped[List[User]] = relationship(
        secondary="user_roles", back_populates="roles", lazy="selectin"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles", lazy="selectin"
    )


class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # e.g. "tasks.read"
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    roles: Mapped[List[Role]] = relationship(
        secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )


class UserRole(Base):
    """
    Ассоциация Пользователь↔Роль.
    Держим как mapped-class, чтобы на него можно было ссылаться из кода (seeds и т.д.).
    """
    __tablename__ = "user_roles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_pair"),
        Index("ix_user_roles_user", "user_id"),
        Index("ix_user_roles_role", "role_id"),
    )


class RolePermission(Base):
    """
    Ассоциация Роль↔Разрешение.
    """
    __tablename__ = "role_permissions"
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
        Index("ix_role_permissions_role", "role_id"),
        Index("ix_role_permissions_perm", "permission_id"),
    )


# ───────────────────────── Domain: Processes / Tasks ─────────────────────────

class Process(TimestampMixin, Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active")

    tasks: Mapped[List["Task"]] = relationship(back_populates="process", lazy="selectin")


class TaskType(TimestampMixin, Base):
    __tablename__ = "task_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # e.g. "bug", "request"
    title: Mapped[str] = mapped_column(String(200))
    # JSON_AUTO — JSONB в Postgres, JSON в SQLite
    default_fields: Mapped[dict] = mapped_column(JSON, default=dict)           # схема/дефолты для кастом-полей
    statuses: Mapped[List[str]] = mapped_column(JSON, default=list)            # допустимые статусы
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)         # опционально: специфичные права


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)

    process_id: Mapped[Optional[int]] = mapped_column(ForeignKey("processes.id", ondelete="SET NULL"))
    type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_types.id", ondelete="SET NULL"))
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    fields: Mapped[dict] = mapped_column(JSON, default=dict)  # произвольные поля по TaskType

    process: Mapped[Optional[Process]] = relationship(back_populates="tasks", lazy="selectin")
    type: Mapped[Optional[TaskType]] = relationship(lazy="selectin")
    assignee: Mapped[Optional[User]] = relationship(back_populates="tasks_assigned", lazy="selectin")

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_title", "title"),
    )


# ───────────────────────── Forms (no/low-code) ─────────────────────────

class FormDef(TimestampMixin, Base):
    """
    Описание формы (схема, валидация, UI-метаданные).
    """
    __tablename__ = "form_defs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # e.g. "vacation_request"
    title: Mapped[str] = mapped_column(String(200))
    schema: Mapped[dict] = mapped_column(JSON, default=dict)                # JSON-схема/конфиг
    meta: Mapped[dict] = mapped_column(JSON, default=dict)                  # UI hints, permissions, etc.


class FormSubmission(TimestampMixin, Base):
    """
    Заполненная форма (ответы), связана с FormDef.
    """
    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("form_defs.id", ondelete="CASCADE"))
    data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    form: Mapped[FormDef] = relationship(lazy="selectin")
    created_by: Mapped[Optional[User]] = relationship(lazy="selectin")


__all__ = [
    "Base",
    "TimestampMixin",
    # RBAC
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # Domain
    "Process",
    "TaskType",
    "Task",
    # Forms
    "FormDef",
    "FormSubmission",
]
