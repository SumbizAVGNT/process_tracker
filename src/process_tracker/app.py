# src/process_tracker/app.py
from __future__ import annotations

import flet as ft
from .core.logging import setup_logging, logger
from .core.config import settings
from .ui.router import handle_route_change
from .server import start_api_server

# --- Flet compatibility shims (версии отличаются именами) ---
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
    ft.icons = ft.Icons  # type: ignore[attr-defined]
if not hasattr(ft, "colors") and hasattr(ft, "Colors"):
    ft.colors = ft.Colors  # type: ignore[attr-defined]
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"):
    ft.alignment = ft.Alignment  # type: ignore[attr-defined]

# Цвета/утилиты, которых может не быть в старых версиях
if hasattr(ft, "colors"):
    if not hasattr(ft.colors, "SURFACE_VARIANT"):
        setattr(ft.colors, "SURFACE_VARIANT", "#2c2c2c")
    if not hasattr(ft.colors, "SURFACE"):
        setattr(ft.colors, "SURFACE", "#121212")
    if not hasattr(ft.colors, "with_opacity"):
        def _with_opacity(opacity: float, color: str) -> str:
            return color
        setattr(ft.colors, "with_opacity", staticmethod(_with_opacity))  # type: ignore[misc]

# ---- Алиасы для иконок, отсутствующих в конкретной сборке Flet ----
def _icons_ns():
    return getattr(ft, "icons", None) or getattr(ft, "Icons", None)

def _ensure_icon(name: str, *fallbacks: str) -> None:
    ns = _icons_ns()
    if ns is None:
        return
    if hasattr(ns, name):
        return
    for fb in fallbacks:
        if hasattr(ns, fb):
            setattr(ns, name, getattr(ns, fb))
            return
    # последний шанс — INFO
    if hasattr(ns, "INFO"):
        setattr(ns, name, getattr(ns, "INFO"))

# Частые проблемные имена → сюда добавляем при необходимости
_ensure_icon("PENDING_ACTION", "SCHEDULE", "HOURGLASS_EMPTY", "HOURGLASS_TOP_OUTLINED", "LIST")
_ensure_icon("TASK_ALT_OUTLINED", "TASK_ALT", "CHECK_CIRCLE")
_ensure_icon("ROCKET_LAUNCH", "ROCKET_LAUNCH_OUTLINED", "ROCKET", "PLAY_ARROW")

def main(page: ft.Page):
    setup_logging()

    # API-сервер FastAPI в фоне
    start_api_server()  # 127.0.0.1:8787

    page.title = "Процесс Трекер"
    page.theme_mode = ft.ThemeMode.DARK
    page.on_route_change = lambda r: handle_route_change(page)

    logger.info("app_started", env=settings.app_env)
    page.go(page.route or "/")

def run():
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)

if __name__ == "__main__":
    run()
