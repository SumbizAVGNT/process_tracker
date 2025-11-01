from __future__ import annotations
import flet as ft

from ..components.shell import page_scaffold
from ..components.theme import card
from ..components.forms import toast

def view(page: ft.Page) -> ft.View:
    theme_dd = ft.Dropdown(
        label="Тема",
        options=[ft.dropdown.Option("dark", "Тёмная"), ft.dropdown.Option("light", "Светлая")],
        value="dark", dense=True, width=240,
    )
    density_dd = ft.Dropdown(
        label="Плотность интерфейса",
        options=[ft.dropdown.Option("comfortable", "Комфортная"), ft.dropdown.Option("compact", "Компактная")],
        value="comfortable", dense=True, width=240,
    )
    save_btn = ft.FilledButton("Сохранить", icon=ft.icons.SAVE, on_click=lambda _e: toast(page, "Настройки сохранены", kind="success"))

    prefs = card(
        "Интерфейс",
        ft.Column([ft.Row([theme_dd, density_dd], spacing=10), save_btn], spacing=10, tight=True),
        icon=ft.icons.STYLE,
    )

    account = card(
        "Аккаунт",
        ft.Column(
            [
                ft.Text("Изменение пароля и email — позже 😉", color=ft.colors.ON_SURFACE_VARIANT),
            ],
            spacing=8, tight=True,
        ),
        icon=ft.icons.PERSON,
    )

    content = ft.Column([prefs, account], spacing=12, tight=True)
    return page_scaffold(page, title="Настройки", route="/settings", body=content)
