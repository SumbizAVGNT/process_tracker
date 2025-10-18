# src/process_tracker/ui/pages/login.py

from __future__ import annotations

import flet as ft

from ...db.session import AsyncSessionLocal
from ...db.dal.user_repo import UserRepo
from ...core.security import verify_password
from ..state import state
from ..components.forms import async_button, toast


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — вход"

    email = ft.TextField(
        label="Email",
        autofocus=True,
        keyboard_type=ft.KeyboardType.EMAIL,
        expand=True,
    )
    password = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=True,
        expand=True,
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
        success_message=None,  # сообщаем сами при успехе
        error_message="Ошибка входа",
        width=160,
    )

    form = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Процесс Трекер", size=26, weight="bold"),
                ft.Text("Войдите, чтобы продолжить", size=14, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Divider(height=8, color="transparent"),
                email,
                password,
                ft.Row([login_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=12,
            tight=True,
        ),
        padding=20,
        width=420,
        bgcolor=ft.colors.with_opacity(0.03, ft.colors.SURFACE_VARIANT),
        border_radius=12,
    )

    return ft.View(
        route="/",
        controls=[
            ft.Container(
                content=form,
                expand=True,
                alignment=ft.alignment.center,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
