# src/process_tracker/app.py

from __future__ import annotations

import flet as ft
from .core.logging import setup_logging, logger
from .core.config import settings
from .ui.router import handle_route_change
from .server import start_api_server

# Dev-bootstrap БД и сид RBAC
from .db.migration import ensure_alembic_tree, upgrade_head_with_bootstrap
from .db.session import AsyncSessionLocal
from .db.seed import seed_rbac


async def _dev_seed_rbac():
    try:
        async with AsyncSessionLocal() as s:
            await seed_rbac(s)
        logger.info("rbac_seeded_on_startup")
    except Exception as e:  # noqa: BLE001
        logger.warning("rbac_seed_failed", error=str(e))


def main(page: ft.Page):
    # Логи
    setup_logging()

    # Dev-инициализация схемы (однократно создаст миграции и накатит)
    if settings.is_dev:
        try:
            ensure_alembic_tree()
            upgrade_head_with_bootstrap()
            # сидим RBAC неблокирующе
            page.run_task(_dev_seed_rbac())
        except Exception as e:  # noqa: BLE001
            logger.warning("dev_bootstrap_failed", error=str(e))

    # API-сервер FastAPI в фоне
    start_api_server()  # 127.0.0.1:8787

    # Параметры окна/приложения
    page.title = "Процесс Трекер"
    page.theme_mode = ft.ThemeMode.DARK
    page.on_route_change = lambda r: handle_route_change(page)

    logger.info("app_started", env=settings.app_env)
    page.go(page.route or "/")


def run():
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)


if __name__ == "__main__":
    run()
