# src/process_tracker/db/__init__.py
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine
from .models import Base  # важно: регистрирует модели/индексы


async def init_db() -> None:
    """
    Идемпотентная инициализация схемы:
    - включает SQLite PRAGMA
    - create_all с защитой от повторного создания уже существующих объектов
    """
    async with engine.begin() as conn:
        # SQLite тюнинг + внешние ключи
        if engine.url.get_backend_name().startswith("sqlite"):
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
        try:
            # SQLAlchemy сам делает checkfirst, но на SQLite иногда всплывают гонки/несоответствия.
            # Перехватываем «already exists» и считаем это нормой при повторном запуске.
            await conn.run_sync(Base.metadata.create_all)
        except OperationalError as e:
            if "already exists" in str(e).lower():
                # индекс/таблица уже создан(а) — ок
                return
            raise


async def drop_db() -> None:
    """Удаление схемы (мягко, с игнорированием отсутствующих объектов)."""
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except OperationalError:
            # например, если таблиц уже нет
            pass
