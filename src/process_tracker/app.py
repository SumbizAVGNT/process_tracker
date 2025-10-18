# src/process_tracker/app.py
from __future__ import annotations

import flet as ft
from .core.logging import setup_logging, logger
from .core.config import settings
from .ui.router import handle_route_change
from .server import start_api_server

# --- Flet compatibility shims (разные версии Flet) ---
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
    ft.icons = ft.Icons  # type: ignore[attr-defined]
if not hasattr(ft, "colors") and hasattr(ft, "Colors"):
    ft.colors = ft.Colors  # type: ignore[attr-defined]
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"):
    ft.alignment = ft.Alignment  # type: ignore[attr-defined]

# Fallback для отсутствующих цветов/утилит
if hasattr(ft, "colors"):
    if not hasattr(ft.colors, "SURFACE_VARIANT"):
        # тёмно-серый для фона "variant"
        setattr(ft.colors, "SURFACE_VARIANT", "#2c2c2c")
    if not hasattr(ft.colors, "SURFACE"):
        # базовый фон в тёмной теме
        setattr(ft.colors, "SURFACE", "#121212")
    if not hasattr(ft.colors, "with_opacity"):
        # на старых версиях — просто возвращаем цвет без прозрачности
        def _with_opacity(opacity: float, color: str) -> str:  # type: ignore[override]
            return color
        setattr(ft.colors, "with_opacity", staticmethod(_with_opacity))  # type: ignore[misc]


def main(page: ft.Page):
    setup_logging()

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
