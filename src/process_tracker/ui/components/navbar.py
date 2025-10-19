# src/process_tracker/ui/components/navbar.py
from __future__ import annotations

import flet as ft
from ..state import state

# ── compat ───────────────────────────────────────────────────────────────────
# Поддержка альтернативных имён в старых версиях Flet
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

def _icon(name: str | None):
    return getattr(ft.icons, name, None) if isinstance(name, str) else name

# ── chip ─────────────────────────────────────────────────────────────────────
def _chip(text: str, icon: str | None, *, active: bool, on_click) -> ft.Control:
    """
    Адаптивная «таб-кнопка» навигации:
    - Filled при active, Outlined иначе
    - Безопасные стили (shape/padding), чтобы не падать на старых Flet
    """
    base = ft.FilledButton if active else ft.OutlinedButton
    style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10),
        padding=ft.padding.symmetric(10, 14),
    )
    return base(
        text,
        icon=_icon(icon),
        on_click=on_click,
        height=36,
        style=style,
    )

# ── navbar ───────────────────────────────────────────────────────────────────
def navbar(page: ft.Page, active_route: str) -> ft.Container:
    """
    Горизонтальная навигация по основным разделам.
    • Скрывает «Настройки» если нет разрешения settings.read
    • Скролл по горизонтали на узких экранах
    """
    items: list[tuple[str, str, str]] = [
        ("/dashboard", "Дашборд", "DASHBOARD"),
        ("/processes", "Процессы", "TIMELINE"),
        ("/blueprint", "Блюпринт", "HUB_OUTLINED"),  # ⬅️ есть в скрине — оставить
        ("/tasks/create", "Создать задачу", "ADD_TASK"),
    ]
    if state.can("settings.read"):
        items.append(("/settings", "Настройки", "SETTINGS"))
    # Функция сравнения активного маршрута (строгое равенство; можно заменить на startswith)
    def _is_active(route: str) -> bool:
        return (active_route or "").rstrip("/") == (route or "").rstrip("/")

    row = ft.Row(
        [
            _chip(
                title, icon,
                active=_is_active(route),
                on_click=lambda _e, r=route: page.go(r),
            )
            for route, title, icon in items
        ],
        spacing=10,
        wrap=False,
    )

    # Горизонтальный скролл — безопасное значение для разных версий Flet
    try:
        row.scroll = ft.ScrollMode.AUTO
    except Exception:
        pass

    return ft.Container(
        row,
        padding=ft.padding.symmetric(8, 8),
    )
