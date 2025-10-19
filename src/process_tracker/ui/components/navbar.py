from __future__ import annotations

import flet as ft

# Совместимость с разными версиями Flet: icons/Icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]


def _chip_control(
    page: ft.Page,
    *,
    text: str,
    icon: str | None,
    selected: bool,
    route: str,
) -> ft.Control:
    """
    Возвращает «чип»-контрол с on_click=page.go(route), совместимый со старыми Flet.
    Порядок попыток:
      1) FilterChip
      2) Chip
      3) Кастомный контейнер
    """
    def _go(_e=None):
        try:
            page.go(route)
        except Exception:
            # на всякий
            pass

    # 1) Современный FilterChip
    if hasattr(ft, "FilterChip"):
        return ft.FilterChip(
            label=text,
            selected=selected,
            on_select=lambda _e: _go(),
            icon=icon,
        )

    # 2) Более старый Chip
    if hasattr(ft, "Chip"):
        return ft.Chip(
            label=ft.Text(text),
            leading=ft.Icon(icon) if icon else None,
            selected=selected,
            on_click=_go,
        )

    # 3) Кастомный фолбэк
    return ft.GestureDetector(
        on_tap=_go,
        content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=16) if icon else ft.Container(width=0),
                    ft.Text(text, size=13, weight="w500"),
                ],
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(8, 10),
            border_radius=18,
            bgcolor=(
                ft.colors.with_opacity(0.14, ft.colors.PRIMARY)
                if selected
                else ft.colors.with_opacity(0.06, ft.colors.SURFACE)
            ),
            border=ft.border.all(
                1,
                ft.colors.with_opacity(
                    0.22 if selected else 0.10, ft.colors.ON_SURFACE
                ),
            ),
        ),
    )


def navbar(page: ft.Page, active_route: str = "/dashboard") -> ft.Container:
    """
    Верхняя навигация приложения.
    """
    items = [
        ("/dashboard", "Дашборд", getattr(ft.icons, "SPACE_DASHBOARD_OUTLINED", None) or ft.icons.DASHBOARD_OUTLINED),
        ("/processes", "Процессы", getattr(ft.icons, "LIST_ALT_OUTLINED", None) or ft.icons.LIST),
        ("/tasks/create", "Новая задача", getattr(ft.icons, "ADD_TASK", None) or ft.icons.ADD),
        ("/settings", "Настройки", getattr(ft.icons, "SETTINGS_OUTLINED", None) or ft.icons.SETTINGS),
    ]

    chips = [
        _chip_control(
            page,
            text=title,
            icon=icon,
            selected=(route == active_route),
            route=route,
        )
        for route, title, icon in items
    ]

    bar = ft.Row(
        controls=chips,
        spacing=8,
        wrap=True,
    )

    return ft.Container(
        content=bar,
        padding=ft.padding.symmetric(10, 14),
        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE),
        border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE))),
    )
