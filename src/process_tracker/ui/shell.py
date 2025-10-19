from __future__ import annotations
import flet as ft
from ..state import state

# shims для старых версий Flet
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]
if not hasattr(ft, "colors") and hasattr(ft, "Colors"):  # pragma: no cover
    ft.colors = ft.Colors  # type: ignore[attr-defined]
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"):  # pragma: no cover
    ft.alignment = ft.Alignment  # type: ignore[attr-defined]
if hasattr(ft, "colors") and not hasattr(ft.colors, "with_opacity"):  # pragma: no cover
    def _with_opacity(opacity: float, color: str) -> str:
        return color
    ft.colors.with_opacity = staticmethod(_with_opacity)  # type: ignore

MAX_W = 1180

def _nav_button(text: str, route: str, active_route: str, icon: str | None) -> ft.Container:
    is_active = (route == active_route)
    base = ft.TextButton(
        text,
        icon=icon,
        on_click=lambda _: ft.Page.current.go(route) if ft.Page.current else None,
    )
    return ft.Container(
        content=base,
        bgcolor=ft.colors.with_opacity(0.06 if is_active else 0.0, ft.colors.SURFACE),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        ink=True,
    )

def topbar(page: ft.Page, active_route: str) -> ft.Container:
    user = state.user_email or "Гость"
    nav = ft.Row(
        [
            _nav_button("Дашборд", "/dashboard", active_route, ft.icons.DASHBOARD_OUTLINED if hasattr(ft.icons, "DASHBOARD_OUTLINED") else ft.icons.DASHBOARD),
            _nav_button("Процессы", "/processes", active_route, ft.icons.LIST_ALT if hasattr(ft.icons, "LIST_ALT") else ft.icons.LIST),
            _nav_button("Создать задачу", "/tasks/create", active_route, ft.icons.ADD_CIRCLE_OUTLINE if hasattr(ft.icons, "ADD_CIRCLE_OUTLINE") else ft.icons.ADD),
            _nav_button("Настройки", "/settings", active_route, ft.icons.SETTINGS),
        ],
        spacing=4,
        wrap=False,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    right = ft.Row(
        [
            ft.Icon(ft.icons.HELP_OUTLINE, size=16),
            ft.Text("Справка", color=ft.colors.ON_SURFACE_VARIANT),
            ft.Container(width=16),
            ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=18),
            ft.Text(user, weight="w600"),
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    bar = ft.Row(
        [nav, ft.Container(expand=True), right],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        content=bar,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE),
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE)),
    )

def page_scaffold(page: ft.Page, *, title: str, route: str, body: ft.Control) -> ft.View:
    page.title = f"Процесс Трекер — {title}"
    page.theme_mode = ft.ThemeMode.DARK

    content = ft.Container(
        content=ft.Column(
            [
                topbar(page, route),
                ft.Container(height=14),
                body,
            ],
            spacing=0,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=18, vertical=12),
        alignment=ft.alignment.top_center,
        expand=True,
        width=MAX_W,
    )

    return ft.View(
        route=route,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[content],
    )
