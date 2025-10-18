# src/process_tracker/ui/pages/login.py

from __future__ import annotations

import flet as ft

from ...db.session import AsyncSessionLocal
from ...db.dal.user_repo import UserRepo
from ...core.security import verify_password
from ..state import state
from ..components.forms import async_button, toast


CARD_WIDTH = 520
FIELD_WIDTH = CARD_WIDTH - 48  # с учётом padding=24 слева/справа


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — вход"

    heading = ft.Column(
        [
            ft.Text("Процесс Трекер", size=28, weight="w700"),
            ft.Text("Войдите, чтобы продолжить", size=14, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=6,
    )

    email = ft.TextField(
        label="Email",
        hint_text="name@company.com",
        prefix_icon=ft.icons.EMAIL,
        keyboard_type=ft.KeyboardType.EMAIL,
        width=FIELD_WIDTH,          # фиксируем ширину
        dense=False,
    )
    password = ft.TextField(
        label="Пароль",
        prefix_icon=ft.icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        width=FIELD_WIDTH,          # фиксируем ширину
        dense=False,
    )

    async def do_login():
        e = (email.value or "").strip().lower()
        p = (password.value or "").strip()
        if not e or not p:
            toast(page, "Заполни email и пароль", kind="warn")
            return

        async with AsyncSessionLocal() as s:
            user = await UserRepo(s).get_by_email(e)

        if not user:
            toast(page, "Пользователь не найден", kind="error")
            return

        if not verify_password(p, user.password_hash):
            toast(page, "Неверный пароль", kind="error")
            return

        state.user_email = e
        state.is_authenticated = True
        toast(page, "Вход выполнен", kind="success")
        page.go("/dashboard")

    login_btn = async_button(
        page,
        "Войти",
        task_factory=do_login,
        icon=ft.icons.LOGIN,
        success_message=None,
        error_message="Ошибка входа",
        width=260,
    )

    card = ft.Container(
        content=ft.Column(
            [
                heading,
                ft.Divider(height=8, color="transparent"),
                email,
                password,
                ft.Container(
                    content=ft.Row([login_btn], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=10),
                    width=FIELD_WIDTH,
                ),
            ],
            spacing=14,
            tight=True,               # компактная колонка по контенту
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=CARD_WIDTH,
        padding=ft.padding.all(24),
        border_radius=16,
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )

    return ft.View(
        route="/",
        controls=[
            ft.Container(
                content=card,
                expand=True,
                alignment=ft.alignment.center,
                padding=ft.padding.all(16),
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
