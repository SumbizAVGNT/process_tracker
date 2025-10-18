# src/process_tracker/db/models.py
"""
SQLAlchemy 2.0 (async) модели для «Процесс Трекер».

Содержит базовые сущности:
- User      — пользователь (минимум: email, password_hash, is_active)
- Process   — процесс (название, описание, статус)
- Task      — задача (название, флаг выполнения)

SQLite по умолчанию, но модели совместимы с Postgres/MySQL.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin

from .session import Base


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} active={self.is_active}>"


class Process(TimestampMixin, Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(50), default="new")

    __table_args__ = (Index("ix_processes_title", "title"),)

    def __repr__(self) -> str:
        return f"<Process id={self.id} title={self.title!r} status={self.status!r}>"


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_tasks_title", "title"),)

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} done={self.done}>"
