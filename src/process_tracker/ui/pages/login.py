# src/process_tracker/ui/pages/login.py

from __future__ import annotations

import flet as ft

from ...db.session import AsyncSessionLocal
from ...db.dal.user_repo import UserRepo
from ...core.security import verify_password
from ..state import state
from ..components.forms import async_button, toast

CARD_WIDTH = 440
INNER_GAP = 12


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — вход"

    # ---------- Заголовок карточки ----------
    logo = ft.Container(
        content=ft.Icon(ft.icons.TASK_ALT_OUTLINED, size=28),
        width=44,
        height=44,
        border_radius=22,
        bgcolor=ft.colors.with_opacity(0.12, ft.colors.SURFACE),
        alignment=ft.alignment.center,
    )

    title_block = ft.Column(
        [
            ft.Text("Процесс Трекер", size=26, weight="w700"),
            ft.Text("Войдите, чтобы продолжить", size=13, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        spacing=4,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header = ft.Column(
        [logo, title_block],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ---------- Поля формы ----------
    email = ft.TextField(
        label="Email",
        hint_text="name@company.com",
        prefix_icon=ft.icons.EMAIL,
        width=CARD_WIDTH - 48,  # минус внутренние отступы карточки
        keyboard_type=ft.KeyboardType.EMAIL,
    )

    password = ft.TextField(
        label="Пароль",
        prefix_icon=ft.icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        width=CARD_WIDTH - 48,
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

    # Enter в поле пароля = вход
    password.on_submit = lambda _: page.run_task(do_login)

    login_btn = async_button(
        page,
        "Войти",
        task_factory=do_login,
        icon=ft.icons.LOGIN,
        success_message=None,
        error_message="Ошибка входа",
        width=CARD_WIDTH - 120,
    )

    # ---------- Карточка ----------
    card = ft.Container(
        content=ft.Column(
            [
                header,
                ft.Divider(height=4, color="transparent"),
                email,
                password,
                ft.Container(
                    ft.Row([login_btn], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=6),
                ),
            ],
            spacing=INNER_GAP,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=CARD_WIDTH,
        padding=ft.padding.all(24),
        border_radius=18,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )

    # ---------- Центровка ----------
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
