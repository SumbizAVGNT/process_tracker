from __future__ import annotations
import flet as ft

from ...db.session import AsyncSessionLocal
from ...db.dal.user_repo import UserRepo
from ...core.security import verify_password
from ..state import state
from ..components.forms import async_button, toast
from ..components.theme import card

CARD_WIDTH = 440

def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — вход"

    email = ft.TextField(
        label="Email",
        hint_text="name@company.com",
        prefix_icon=ft.icons.EMAIL,
        width=CARD_WIDTH - 48,
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
            toast(page, "Заполни email и пароль", kind="warning")
            return

        async with AsyncSessionLocal() as s:
            user = await UserRepo(s).get_by_email(e)

        if not user:
            toast(page, "Пользователь не найден", kind="error")
            return
        if not verify_password(p, user.password_hash):
            toast(page, "Неверный пароль", kind="error")
            return

        state.set_auth(email=e, roles=["user"], permissions={"*"})
        toast(page, "Вход выполнен", kind="success")
        page.go("/dashboard")

    password.on_submit = lambda _e: page.run_task(do_login)

    form = card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(ft.icons.TASK_ALT_OUTLINED, size=28),
                            width=44, height=44, border_radius=22,
                            bgcolor=ft.colors.with_opacity(0.12, ft.colors.SURFACE),
                            alignment=ft.alignment.center,
                        ),
                        ft.Column(
                            [ft.Text("Процесс Трекер", size=22, weight="w700"),
                             ft.Text("Войдите, чтобы продолжить", size=12, color=ft.colors.ON_SURFACE_VARIANT)],
                            spacing=2,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=8, color="transparent"),
                email,
                password,
                ft.Container(
                    ft.Row(
                        [async_button(page, "Войти", task_factory=do_login, icon=ft.icons.LOGIN, width=CARD_WIDTH - 120)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.only(top=6),
                ),
            ],
            spacing=12,
        ),
        body=None,  # выше уже передан составной заголовок+форма
        icon=None,
    )

    wrapper = ft.Container(content=form, width=CARD_WIDTH, padding=ft.padding.all(0))
    return ft.View("/", [ft.Container(content=wrapper, expand=True, alignment=ft.alignment.center, padding=16)])
