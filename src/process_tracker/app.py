from __future__ import annotations

import asyncio
import threading
import flet as ft

from .core.logging import setup_logging, logger
from .core.config import settings
from .ui.router import handle_route_change
from .server import start_api_server
from .db import init_db  # ⬅️ авто-инициализация схемы БД


# --- Flet compatibility shims (версии отличаются именами) --------------------
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
    ft.icons = ft.Icons  # type: ignore[attr-defined]
if not hasattr(ft, "colors") and hasattr(ft, "Colors"):
    ft.colors = ft.Colors  # type: ignore[attr-defined]
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"):
    ft.alignment = ft.Alignment  # type: ignore[attr-defined]

# Цвета/утилиты, которых может не быть в старых версиях Flet
if hasattr(ft, "colors"):
    if not hasattr(ft.colors, "SURFACE_VARIANT"):
        setattr(ft.colors, "SURFACE_VARIANT", "#2c2c2c")
    if not hasattr(ft.colors, "SURFACE"):
        setattr(ft.colors, "SURFACE", "#121212")


# ---- Алиасы для иконок, отсутствующих в конкретной сборке Flet --------------
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
    if hasattr(ns, "INFO"):  # крайний фоллбек
        setattr(ns, name, getattr(ns, "INFO"))


# Часто используемые алиасы
_ensure_icon("PENDING_ACTION", "SCHEDULE", "HOURGLASS_EMPTY", "LIST")
_ensure_icon("TASK_ALT_OUTLINED", "TASK_ALT", "CHECK_CIRCLE")
_ensure_icon("ROCKET_LAUNCH", "ROCKET_LAUNCH_OUTLINED", "ROCKET", "PLAY_ARROW")
_ensure_icon("DATABASE", "STORAGE", "DATA_EXPLORATION", "BAR_CHART")


def _init_db_blocking() -> None:
    """
    Инициализируем БД максимально безопасно:
    - если event loop уже есть и ЗАПУЩЕН — выполним инициализацию в отдельном потоке (с отдельным loop) и дождёмся
    - если цикла нет — обычный asyncio.run()
    """
    try:
        loop = asyncio.get_running_loop()
        # Если мы тут — цикл уже запущен. Делаем отдельный поток с отдельным loop и БЛОКИРУЕМСЯ до завершения.
        done = threading.Event()

        def _worker():
            try:
                asyncio.run(init_db())
            finally:
                done.set()

        t = threading.Thread(target=_worker, name="init-db", daemon=True)
        t.start()
        # Дожидаемся завершения инициализации, чтобы UI/роутинг стартовал уже с готовой схемой
        done.wait()
    except RuntimeError:
        # Нет активного цикла — обычный путь в контексте Flet Web/Desktop
        asyncio.run(init_db())


def main(page: ft.Page):
    setup_logging()

    # ⬇️ ОБЯЗАТЕЛЬНО: гарантируем схему БД ДО старта UI/роутинга (идемпотентно)
    try:
        _init_db_blocking()
        db_url_display = getattr(settings, "db_url_resolved", getattr(settings, "db_url", "unknown"))
        logger.info("db_auto_initialized", url=db_url_display, env=settings.app_env)
    except Exception:
        logger.exception("db_auto_init_failed")

    # API-сервер FastAPI в фоне (по умолчанию 127.0.0.1:8787)
    try:
        start_api_server()
    except Exception:
        logger.exception("api_server_start_failed")

    # Базовые настройки страницы
    page.title = "Процесс Трекер"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # Роутинг
    page.on_route_change = lambda _e: handle_route_change(page)

    logger.info("app_started", env=settings.app_env)
    page.go(page.route or "/")  # триггерим первичную отрисовку


def _app_view():
    # Совместимость с разными версиями Flet
    try:
        return ft.AppView.WEB_BROWSER
    except Exception:
        return "web_browser"


def run():
    ft.app(target=main, view=_app_view())


if __name__ == "__main__":
    run()
