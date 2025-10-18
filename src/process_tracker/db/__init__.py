from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine
from .models import Base  # ВАЖНО: импортирует все модели и регистрирует их на Base.metadata


async def init_db() -> None:
    """
    Идемпотентная инициализация схемы:
    - включает SQLite PRAGMA
    - пробует create_all()
    - затем гарантированно создаёт каждую таблицу по отдельности с checkfirst=True
    """
    async with engine.begin() as conn:
        # SQLite тюнинг + внешние ключи
        if engine.url.get_backend_name().startswith("sqlite"):
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))

        # 1) общая попытка
        try:
            await conn.run_sync(Base.metadata.create_all)
        except OperationalError as e:
            # Логируем и продолжаем «добивать» точечно
            # (иногда на SQLite всплывает existing index -> не должно блокировать остальные таблицы)
            # print(f"[init_db] create_all warning: {e}")  # можно раскомментировать при отладке
            pass

        # 2) гарантированно создадим недостающие таблицы по одной
        for table in Base.metadata.sorted_tables:
            try:
                await conn.run_sync(table.create, checkfirst=True)
            except OperationalError:
                # если индекс/таблица уже есть — пропускаем
                pass


async def drop_db() -> None:
    """Удаление схемы (мягко, с игнорированием отсутствующих объектов)."""
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except OperationalError:
            pass
