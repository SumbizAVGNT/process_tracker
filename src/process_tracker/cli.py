# src/process_tracker/cli.py
"""
Process Tracker — CLI (stdlib argparse)

Запуск:
  python -m process_tracker.cli --help

DB/миграции:
  python -m process_tracker.cli init-db
  python -m process_tracker.cli drop-db
  python -m process_tracker.cli seed-rbac
  python -m process_tracker.cli migrate              # upgrade head (bootstrap если нет ревизий)
  python -m process_tracker.cli upgrade --to head
  python -m process_tracker.cli downgrade --to -1
  python -m process_tracker.cli current
  python -m process_tracker.cli revision -m "init"

Пользователи:
  python -m process_tracker.cli create-user --email user@example.com --role user --role manager --admin
  # Пароль будет спрошен интерактивно (или передай --password "..." или --password-prompt)

Серверы:
  python -m process_tracker.cli run-api --host 0.0.0.0 --port 8787
  python -m process_tracker.cli run-app
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import logging
from typing import Optional

import uvicorn

from process_tracker.core.logging import setup_logging, logger
from process_tracker.core.config import settings
from process_tracker.core.security import hash_password
from process_tracker.db import init_db, drop_db
from process_tracker.db.session import AsyncSessionLocal
from process_tracker.db.seed import seed_rbac
from process_tracker.db.migration import (
    ensure_alembic_tree,
    upgrade_head_with_bootstrap,
    upgrade as alembic_upgrade,
    downgrade as alembic_downgrade,
    revision as alembic_revision,
    current as alembic_current,
)
from process_tracker.db.dal.user_repo import UserRepo
from process_tracker.db.dal.role_repo import RoleRepo
from process_tracker.server import get_application
from process_tracker.app import run as run_flet_app


# ---------------------- DB / SEED ----------------------

async def cmd_init_db(_args) -> None:
    await init_db()
    logger.info("db_initialized", url=settings.db_url)


async def cmd_drop_db(_args) -> None:
    await drop_db()
    logger.info("db_dropped", url=settings.db_url)


async def cmd_seed_rbac(_args) -> None:
    async with AsyncSessionLocal() as session:
        await seed_rbac(session)
    logger.info("rbac_seeded")


# ---------------------- Alembic ----------------------

def cmd_migrate(args) -> None:
    ensure_alembic_tree()
    if args.bootstrap:
        upgrade_head_with_bootstrap()
    else:
        alembic_upgrade(args.to or "head")
    logger.info("alembic_migrate_done")


def cmd_upgrade(args) -> None:
    ensure_alembic_tree()
    alembic_upgrade(args.to or "head")
    logger.info("alembic_upgrade_done", to=args.to or "head")


def cmd_downgrade(args) -> None:
    ensure_alembic_tree()
    alembic_downgrade(args.to or "-1")
    logger.info("alembic_downgrade_done", to=args.to or "-1")


def cmd_current(_args) -> None:
    ensure_alembic_tree()
    alembic_current(verbose=True)


def cmd_revision(args) -> None:
    ensure_alembic_tree()
    msg = args.message or "change"
    autogen = not args.no_autogenerate
    alembic_revision(message=msg, autogenerate=autogen)
    logger.info("alembic_revision_created", message=msg, autogenerate=autogen)


# ---------------------- Users ----------------------

async def cmd_create_user(args) -> None:
    """
    Создать пользователя и назначить роли.
    Безопасность:
      - пароль читаем из stdin (getpass) по умолчанию, чтобы не светить в истории
      - хэшируем bcrypt (passlib)
    """
    email: str = args.email.strip().lower()
    if "@" not in email or "." not in email:
        raise SystemExit("Неверный email")

    # Пароль: либо из аргумента, либо интерактивный ввод, либо явный prompt
    password = args.password
    if args.password_prompt or not password:
        while True:
            p1 = getpass.getpass("Введите пароль: ")
            p2 = getpass.getpass("Повторите пароль: ")
            if p1 != p2:
                print("Пароли не совпадают, попробуйте снова.")
                continue
            password = p1
            break

    if not password or len(password) < 6:
        raise SystemExit("Пароль должен быть длиной не менее 6 символов")

    roles: list[str] = [r.strip().lower() for r in (args.role or []) if r.strip()]
    if args.admin and "admin" not in roles:
        roles.append("admin")
    if not roles:
        roles = ["user"]

    async with AsyncSessionLocal() as session:
        urepo = UserRepo(session)
        rrepo = RoleRepo(session)

        user = await urepo.get_by_email(email)
        if user:
            if args.force_reset:
                user.password_hash = hash_password(password)
                logger.info("user_password_reset", email=email)
            else:
                logger.info("user_exists", email=email)
        else:
            user = await urepo.create(email=email, password_hash=hash_password(password))
            logger.info("user_created", email=email, id=getattr(user, "id", None))

        # Назначаем роли (создаём недостающие)
        assigned = []
        for role_name in roles:
            role = await rrepo.get_by_name(role_name)
            if not role:
                role = await rrepo.create(role_name, description=f"Auto-created role {role_name}")
            if role not in user.roles:
                user.roles.append(role)
                assigned.append(role_name)

        await session.commit()
        logger.info("user_roles_updated", email=email, roles=[r.name for r in user.roles], newly_assigned=assigned)


# ---------------------- Servers ----------------------

def cmd_run_api(args) -> None:
    host = args.host or settings.api_host
    port = int(args.port or settings.api_port)
    log_level = (args.log_level or settings.log_level).lower()

    app = get_application()
    uvicorn.run(app, host=host, port=port, log_level=log_level)


def cmd_run_app(_args) -> None:
    run_flet_app()


# ---------------------- Parser ----------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="process-tracker", description="Process Tracker CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # DB
    sub.add_parser("init-db", help="Создать таблицы (dev/тест)").set_defaults(func=lambda a: asyncio.run(cmd_init_db(a)))
    sub.add_parser("drop-db", help="Удалить таблицы (dev only)").set_defaults(func=lambda a: asyncio.run(cmd_drop_db(a)))
    sub.add_parser("seed-rbac", help="Заполнить роли/права").set_defaults(func=lambda a: asyncio.run(cmd_seed_rbac(a)))

    # Alembic
    p_mig = sub.add_parser("migrate", help="Upgrade head (по умолчанию bootstrap, если нет ревизий)")
    p_mig.add_argument("--to", dest="to", default=None, help="Цель (по умолчанию head)")
    p_mig.add_argument("--no-bootstrap", dest="bootstrap", action="store_false", help="Не выполнять bootstrap-логику")
    p_mig.set_defaults(func=cmd_migrate, bootstrap=True)

    p_up = sub.add_parser("upgrade", help="alembic upgrade")
    p_up.add_argument("--to", dest="to", default="head", help="Цель (по умолчанию head)")
    p_up.set_defaults(func=cmd_upgrade)

    p_down = sub.add_parser("downgrade", help="alembic downgrade")
    p_down.add_argument("--to", dest="to", default="-1", help="Цель (по умолчанию -1)")
    p_down.set_defaults(func=cmd_downgrade)

    sub.add_parser("current", help="alembic current").set_defaults(func=cmd_current)

    p_rev = sub.add_parser("revision", help="alembic revision")
    p_rev.add_argument("-m", "--message", dest="message", required=True, help="Сообщение ревизии")
    p_rev.add_argument("--no-autogenerate", action="store_true", help="Отключить autogenerate")
    p_rev.set_defaults(func=cmd_revision)

    # Users
    p_user = sub.add_parser("create-user", help="Создать пользователя и назначить роли")
    p_user.add_argument("--email", required=True, help="Email пользователя")
    p_user.add_argument("--password", default=None, help="Пароль (небезопасно хранить в истории, лучше --password-prompt)")
    p_user.add_argument("--password-prompt", action="store_true", help="Запросить пароль интерактивно")
    p_user.add_argument("--role", action="append", help="Роль (можно несколько: --role user --role manager)")
    p_user.add_argument("--admin", action="store_true", help="Также назначить роль admin")
    p_user.add_argument("--force-reset", action="store_true", help="Если пользователь существует — перезаписать пароль")
    p_user.set_defaults(func=lambda a: asyncio.run(cmd_create_user(a)))

    # Servers
    p_api = sub.add_parser("run-api", help="Запустить только API-сервер (FastAPI+Uvicorn)")
    p_api.add_argument("--host", default=None)
    p_api.add_argument("--port", default=None)
    p_api.add_argument("--log-level", default=None, help="debug|info|warning|error")
    p_api.set_defaults(func=cmd_run_api)

    sub.add_parser("run-app", help="Запустить Flet приложение (с API в фоне)").set_defaults(func=cmd_run_app)

    return p


def main(argv: Optional[list[str]] = None) -> None:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    # Стандартный logging root для совместимости с uvicorn/fastapi
    logging.getLogger().setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("cli_start", cmd=args.cmd)
    args.func(args)


if __name__ == "__main__":
    main()
