from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    String,
    Boolean,
    DateTime,
    UniqueConstraint,
    Index,
    MetaData,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Единая схема имен для кросс-СУБД стабильности названий ограничений/индексов
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata_obj


# ---------------------- Mixin'ы ----------------------

class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
        nullable=False,
    )


# ---------------------- Ассоциации ----------------------

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ---------------------- RBAC ----------------------

class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    dangerous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[List["Role"]] = relationship(
        back_populates="permissions",
        secondary=role_permissions,
        lazy="selectin",
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), default=None)

    permissions: Mapped[List["Permission"]] = relationship(
        back_populates="roles",
        secondary=role_permissions,
        lazy="selectin",
    )
    users: Mapped[List["User"]] = relationship(
        back_populates="roles",
        secondary=user_roles,
        lazy="selectin",
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    roles: Mapped[List[Role]] = relationship(
        back_populates="users",
        secondary=user_roles,
        lazy="selectin",
    )


# ---------------------- Domain: Tasks / Processes ----------------------

class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_tasks_title", "title"),
    )


class Process(TimestampMixin, Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(40), default="new", nullable=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_processes_name"),
    )
