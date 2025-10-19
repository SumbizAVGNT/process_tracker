# src/process_tracker/db/__init__.py
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine
from .models import Base  # Важно: импортирует все модели, регистрируя их в Base.metadata

__all__ = ["init_db", "drop_db"]


async def init_db() -> None:
    """
    Идемпотентная инициализация схемы:
      - включает SQLite PRAGMA
      - пробует Base.metadata.create_all()
      - гарантированно создаёт каждую таблицу отдельно с checkfirst=True
    """
    async with engine.begin() as conn:
        # SQLite: включаем внешние ключи и мягкий тюнинг
        if engine.url.get_backend_name().startswith("sqlite"):
            try:
                await conn.execute(text("PRAGMA foreign_keys=ON"))
            except Exception:
                pass
            # На старых/встроенных сборках может не поддерживаться WAL — не считаем это ошибкой
            try:
                await conn.execute(text("PRAGMA journal_mode=WAL"))
            except Exception:
                pass
            try:
                await conn.execute(text("PRAGMA synchronous=NORMAL"))
            except Exception:
                pass

        # 1) Общая попытка
        try:
            # run_sync передаёт sync-connection первым аргументом; checkfirst=True по умолчанию
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
        except OperationalError:
            # Например, если всплыл конфликт индексов — добьём по-таблично ниже
            pass

        # 2) Добиваем по одной таблице (на случай частичных сбоев)
        for table in Base.metadata.sorted_tables:
            try:
                await conn.run_sync(lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True))
            except OperationalError:
                # Уже существует — игнорируем
                pass


async def drop_db() -> None:
    """Удаление всей схемы (мягко, с игнорированием отсутствующих объектов)."""
    async with engine.begin() as conn:
        try:
            await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn))
        except OperationalError:
            pass
