# src/process_tracker/app.py

import flet as ft
from .core.logging import setup_logging, logger
from .core.config import settings
from .ui.router import handle_route_change
from .server import start_api_server


def main(page: ft.Page):
    # Логи и API-сервер
    setup_logging()
    start_api_server()  # FastAPI на 127.0.0.1:8787

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
