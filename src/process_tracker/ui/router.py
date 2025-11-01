# src/process_tracker/ui/router.py
from __future__ import annotations
"""
UI router: безопасное разрешение маршрута → ft.View.
- Нормализуем route (срезаем query/anchor, убираем лишние слэши)
- Защищаем приватные маршруты (RBAC/авторизация)
- Импорт страниц устойчив к ошибкам (даёт аккуратный 500-вид)
- 404 для неизвестных URL
"""

from typing import Callable
from urllib.parse import urlparse
import traceback
import flet as ft

from .state import state
from ..core.logging import logger


# ---------- helpers ----------

def _norm_route(raw: str | None) -> str:
    """Оставляем только path, без query/hash; убираем хвостовой слэш (кроме '/')."""
    path = (urlparse(raw or "/").path or "/")  # '/a?x=1' -> '/a'
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path or "/"


# Префиксы приватных зон (любые вложенные пути тоже приватные)
_PROTECTED_PREFIXES: tuple[str, ...] = (
    "/dashboard",
    "/processes",
    "/settings",
    "/tasks",
    "/forms",
    "/workflows",
    "/blueprint",   # раздел с вкладками
    # дополнительные разделы
    "/users",
    "/templates",
    "/webhooks",
    "/views",
    "/audit",
    "/files",
)


def _is_protected(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") for p in _PROTECTED_PREFIXES)


def _safe_view(factory: Callable[[ft.Page], ft.View], page: ft.Page) -> ft.View:
    """Выполнить вызов view() страницы безопасно, вернув 500 при исключении."""
    try:
        return factory(page)
    except Exception as e:  # noqa: BLE001
        logger.error("ui_view_error", view=getattr(factory, "__name__", "view"), route=page.route, exc_info=True)
        traceback.print_exc()
        return _error_500(page, str(e))


def _error_404(page: ft.Page, route: str) -> ft.View:
    return ft.View(
        route="/404",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Страница не найдена", size=22, weight="w700"),
                        ft.Text(f"Маршрут: {route}", color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Row(
                            [
                                ft.FilledButton("На главную", icon=ft.icons.HOME, on_click=lambda _: page.go("/")),
                                ft.OutlinedButton(
                                    "Назад",
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=lambda _: page.go("/dashboard" if state.is_authenticated else "/"),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=20,
                expand=True,
                alignment=ft.alignment.center,
            )
        ],
    )


def _error_500(page: ft.Page, message: str) -> ft.View:
    return ft.View(
        route="/500",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Ошибка интерфейса", size=22, weight="w700"),
                        ft.Text(message, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Row(
                            [
                                ft.FilledButton(
                                    "Обновить",
                                    icon=ft.icons.REFRESH,
                                    on_click=lambda _: page.go(_norm_route(page.route)),
                                ),
                                ft.OutlinedButton("На главную", icon=ft.icons.HOME, on_click=lambda _: page.go("/")),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=20,
                expand=True,
                alignment=ft.alignment.center,
            )
        ],
    )


# ---------- core ----------

def _resolve_view(page: ft.Page, route: str) -> ft.View:
    path = _norm_route(route)

    # Logout alias (удобно иметь)
    if path == "/logout":
        state.clear_auth()
        return ft.View(route="/", controls=[])

    # Доступ к приватным зонам только для авторизованных
    if _is_protected(path) and not state.is_authenticated:
        path = "/"

    # Корень/логин
    if path in ("/", "/login"):
        from .pages import login as _login
        return _safe_view(_login.view, page)

    # Дашборд
    if path == "/dashboard":
        from .pages import dashboard as _dashboard
        return _safe_view(_dashboard.view, page)

    # Процессы
    if path == "/processes":
        from .pages import processes as _proc
        return _safe_view(_proc.view, page)

    # Формы
    if path == "/forms":
        from .pages import forms as _forms
        return _safe_view(_forms.view, page)

    # Воркфлоу
    if path == "/workflows":
        from .pages import workflows as _wf
        return _safe_view(_wf.view, page)

    # Блюпринт (включая специальный конструктор /blueprint/designer)
    if path == "/blueprint" or path.startswith("/blueprint/"):
        if path == "/blueprint/designer" or path.startswith("/blueprint/designer"):
            from .pages import blueprint_designer as _bpd
            return _safe_view(_bpd.view, page)

        from .pages import blueprint as _bp
        return _safe_view(_bp.view, page)

    # Пользователи
    if path == "/users":
        from .pages import users as _users
        return _safe_view(_users.view, page)

    # Шаблоны
    if path == "/templates":
        from .pages import templates as _tpl
        return _safe_view(_tpl.view, page)

    # Вебхуки
    if path == "/webhooks":
        from .pages import webhooks as _wh
        return _safe_view(_wh.view, page)

    # Представления
    if path == "/views":
        from .pages import views as _views
        return _safe_view(_views.view, page)

    # Аудит
    if path == "/audit":
        from .pages import audit as _audit
        return _safe_view(_audit.view, page)

    # Файлы
    if path == "/files":
        from .pages import files as _files
        return _safe_view(_files.view, page)

    # Настройки
    if path == "/settings":
        from .pages import settings as _settings
        return _safe_view(_settings.view, page)

    # Создать задачу
    if path in ("/tasks/create", "/task/create"):
        from .pages import task_create as _tc
        return _safe_view(_tc.view, page)

    # Неизвестный путь
    return _error_404(page, path)


def handle_route_change(page: ft.Page) -> None:
    try:
        target_view = _resolve_view(page, page.route or "/")
        # одно присваивание — нет "дёргания" стека
        page.views[:] = [target_view]
        page.update()
        logger.info("ui_route_ok", route=page.route)
    except Exception as e:  # noqa: BLE001
        logger.error("ui_route_error", route=page.route, exc_info=True)
        traceback.print_exc()
        page.views[:] = [_error_500(page, str(e))]
        page.update()
