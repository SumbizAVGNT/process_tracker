# src/process_tracker/db/migration.py
"""
Утилиты для Alembic:
- ensure_alembic_tree() — создаёт минимальную структуру миграций (env.py, versions/)
- revision(message, autogenerate=True) — создать ревизию
- upgrade(target="head") — применить миграции
- downgrade(target="-1") — откатить
- current() — показать текущую ревизию
- upgrade_head_with_bootstrap() — bootstrap: если нет ревизий — создать автогенерируемую "init" и накатить

Работает с async SQLAlchemy: env.py использует наш engine из process_tracker.db.session.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

from ..core.config import settings

# Путь к каталогу миграций в пакете
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
VERSIONS_DIR = MIGRATIONS_DIR / "versions"
ENV_PY = MIGRATIONS_DIR / "env.py"


def ensure_alembic_tree() -> None:
    """
    Создаёт минимальную структуру Alembic, если ещё не создана.
    Пишет env.py, который берёт target_metadata и engine из нашего пакета.
    """
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    if not ENV_PY.exists():
        ENV_PY.write_text(_ENV_TEMPLATE, encoding="utf-8")


def get_alembic_config() -> Config:
    """
    Вернуть объект Config с нужными параметрами (без alembic.ini).
    """
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    # URL нужен для offline режима; online режим использует наш engine из env.py
    cfg.set_main_option("sqlalchemy.url", settings.db_url)
    # Опционально — настраиваем имя каталога версий
    cfg.set_main_option("version_locations", str(VERSIONS_DIR))
    return cfg


def has_revisions() -> bool:
    if not VERSIONS_DIR.exists():
        return False
    return any(p.suffix == ".py" for p in VERSIONS_DIR.iterdir())


def revision(message: str, autogenerate: bool = True) -> None:
    ensure_alembic_tree()
    cfg = get_alembic_config()
    command.revision(cfg, message=message, autogenerate=autogenerate)


def upgrade(target: str = "head") -> None:
    ensure_alembic_tree()
    cfg = get_alembic_config()
    command.upgrade(cfg, target)


def downgrade(target: str = "-1") -> None:
    ensure_alembic_tree()
    cfg = get_alembic_config()
    command.downgrade(cfg, target)


def stamp(target: str = "head") -> None:
    ensure_alembic_tree()
    cfg = get_alembic_config()
    command.stamp(cfg, target)


def current(verbose: bool = True) -> None:
    ensure_alembic_tree()
    cfg = get_alembic_config()
    command.current(cfg, verbose=verbose)


def upgrade_head_with_bootstrap() -> None:
    """
    Bootstrap-помощник: если нет ни одной ревизии — создаёт "init" с autogenerate и применяет её.
    Иначе просто делает upgrade head.
    """
    ensure_alembic_tree()
    if not has_revisions():
        revision("init", autogenerate=True)
    upgrade("head")


# ----------------------- Шаблон env.py -----------------------

_ENV_TEMPLATE = r'''# -*- coding: utf-8 -*-
"""
Async Alembic environment for Process Tracker.

Использует:
- settings.db_url для offline режима
- async engine из process_tracker.db.session для online режима
- target_metadata = Base.metadata для автогенерации миграций
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig  # noqa: F401

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from process_tracker.core.config import settings
from process_tracker.db.session import engine, Base

# Alembic Config object
config = context.config

# Метаданные моделей для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.db_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # важно для SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Синхронная секция, выполняемая в run_sync()."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # важно для SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


def run() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run()
'''
