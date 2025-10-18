# src/process_tracker/ui/components/navbar.py

from __future__ import annotations

import flet as ft
from ..state import state


def _is_active(page: ft.Page, route: str) -> bool:
    return (page.route or "/") == route


def _nav_button(page: ft.Page, label: str, route: str, icon: ft.icons.Icon):
    def _go(_):
        page.go(route)

    return ft.TextButton(
        content=ft.Row(
            [ft.Icon(icon, size=16), ft.Text(label)],
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(8, 10),
            bgcolor={
                ft.ControlState.DEFAULT: ft.colors.with_opacity(0.0, ft.colors.SURFACE_VARIANT),
                ft.ControlState.HOVERED: ft.colors.with_opacity(0.08, ft.colors.SURFACE_VARIANT),
            },
            color=ft.colors.ON_SURFACE,
        ),
        on_click=_go,
    )


def _nav_chip(page: ft.Page, label: str, route: str, icon_name: str):
    """Чип с подсветкой текущего маршрута."""
    active = _is_active(page, route)
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon_name, size=16),
                ft.Text(label, weight="bold" if active else "normal"),
            ],
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=lambda _: page.go(route),
        padding=ft.padding.symmetric(8, 10),
        bgcolor=ft.colors.PRIMARY if active else ft.colors.with_opacity(0.04, ft.colors.SURFACE_VARIANT),
        border_radius=8,
        ink=True,
    )


def navbar(page: ft.Page) -> ft.Container:
    """
    Верхняя панель навигации для web.
    Использование:
        page.appbar = navbar(page)  # либо добавляйте в начало View
    """
    # Левая часть — логотип/название
    left = ft.Row(
        [
            ft.Icon(ft.icons.TASK_ALT_OUTLINED, size=20),
            ft.Text("Процесс Трекер", size=16, weight="w700"),
        ],
        spacing=8,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Центр — основные маршруты
    center = ft.Row(
        [
            _nav_chip(page, "Дашборд", "/dashboard", ft.icons.DASHBOARD_OUTLINED),
            _nav_chip(page, "Задачи", "/processes", ft.icons.CHECKLIST),
            # _nav_chip(page, "Настройки", "/settings", ft.icons.SETTINGS_OUTLINED),  # добавим страницу позже
        ],
        spacing=6,
        tight=True,
        wrap=True,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Правая часть — тема и аккаунт
    theme_switch = ft.IconButton(
        icon=ft.icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.icons.LIGHT_MODE,
        tooltip="Переключить тему",
        on_click=lambda _: _toggle_theme(page),
    )

    if state.is_authenticated and state.user_email:
        account = ft.Row(
            [
                ft.CircleAvatar(content=ft.Text(state.user_email[:1].upper()), radius=14),
                ft.Text(state.user_email, size=12),
                ft.TextButton(
                    "Выйти",
                    on_click=lambda _: _logout(page),
                ),
            ],
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    else:
        account = ft.TextButton("Войти", on_click=lambda _: page.go("/"))

    right = ft.Row(
        [theme_switch, account],
        spacing=8,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Грид: left | center | right
    bar = ft.ResponsiveRow(
        controls=[
            ft.Container(left, col={"xs": 12, "md": 3}),
            ft.Container(center, col={"xs": 12, "md": 6}),
            ft.Container(right, col={"xs": 12, "md": 3}, alignment=ft.alignment.center_right),
        ],
        columns=12,
        run_spacing=6,
    )

    return ft.Container(
        content=bar,
        padding=ft.padding.symmetric(10, 12),
        bgcolor=ft.colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE))),
    )


def _toggle_theme(page: ft.Page):
    page.theme_mode = (
        ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
    )
    # Обновляем и иконку переключателя
    page.update()


def _logout(page: ft.Page):
    from ..state import state as st
    st.is_authenticated = False
    st.user_email = None
    page.go("/")
