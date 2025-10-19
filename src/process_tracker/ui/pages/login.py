from __future__ import annotations
import flet as ft

from ...db.session import AsyncSessionLocal
from ...db.dal.user_repo import UserRepo
from ...core.security import verify_password
from ..state import state

# Локальные помощники — без зависимости от theme.card
def _alpha(c: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, c)
    except Exception:
        return c

def brand_gradient() -> ft.LinearGradient:
    return ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[_alpha(ft.colors.BLUE_ACCENT_400, 0.25), _alpha(ft.colors.PURPLE_ACCENT_200, 0.18)],
    )

def glass_card(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        border=ft.border.all(1, _alpha(getattr(ft.colors, "ON_SURFACE", ft.colors.WHITE), 0.08)),
        border_radius=16,
        bgcolor=_alpha(getattr(ft.colors, "SURFACE", ft.colors.BLUE_GREY_900), 0.06),
        shadow=ft.BoxShadow(blur_radius=16, spread_radius=1,
                            color=_alpha(ft.colors.BLACK, 0.35), offset=ft.Offset(0, 6)),
    )

CARD_WIDTH = 560


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — вход"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.colors.BLACK
    page.padding = 0

    # Header
    header = ft.Row(
        [
            ft.Container(
                content=ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=26, color=ft.colors.BLUE_ACCENT_100),
                width=48, height=48, border_radius=14,
                bgcolor=_alpha(ft.colors.BLUE_ACCENT_400, 0.18),
                alignment=ft.alignment.center,
            ),
            ft.Column(
                [
                    ft.Text("Процесс Трекер", size=24, weight="w800"),
                    ft.Text("Войдите, чтобы продолжить", size=13,
                            color=getattr(ft.colors, "ON_SURFACE_VARIANT", ft.colors.GREY_500)),
                ],
                spacing=2,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Fields
    email = ft.TextField(
        label="Email",
        hint_text="name@company.com",
        prefix_icon=getattr(ft.icons, "MAIL_OUTLINED", ft.icons.EMAIL),
        width=CARD_WIDTH - 48,   # ← фиксированная ширина вместо expand=True
        dense=True,
    )
    from ..components.password_field import PasswordField
    password = PasswordField(label="Пароль", dense=True)

    # Actions
    async def do_login():
        from ..components.forms import toast
        e = (email.value or "").strip().lower()
        p = (password.value or "").strip()
        if not e or not p:
            toast(page, "Заполни email и пароль", kind="warning"); return
        async with AsyncSessionLocal() as s:
            user = await UserRepo(s).get_by_email(e)
        if not user:
            toast(page, "Пользователь не найден", kind="error"); return
        if not verify_password(p, user.password_hash):
            toast(page, "Неверный пароль", kind="error"); return
        state.set_auth(email=e, roles=["user"], permissions={"*"})
        toast(page, "Вход выполнен", kind="success")
        page.go("/dashboard")

    password.on_submit = lambda _e: page.run_task(do_login)
    from ..components.forms import async_button

    actions = ft.Column(
        [
            ft.Container(content=async_button(page, "Войти", task_factory=do_login, icon="LOGIN"),
                         width=CARD_WIDTH - 48),
            ft.Row(
                [
                    ft.TextButton("Забыли пароль?", on_click=lambda _: None),
                    ft.Container(expand=True),
                    ft.Text("Нет аккаунта? ", size=12,
                            color=getattr(ft.colors, "ON_SURFACE_VARIANT", ft.colors.GREY_500)),
                    ft.TextButton("Связаться с админом", on_click=lambda _: None),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
        ],
        spacing=8,
    )

    # Card content
    form_inner = ft.Column(
        [
            header,
            ft.Container(height=12),
            email,
            password,
            ft.Container(height=8),
            actions,
        ],
        spacing=12,
        tight=True,
    )

    form_card = glass_card(ft.Container(content=form_inner, padding=22))
    form = ft.Container(content=form_card, width=CARD_WIDTH)

    # Background + centering
    bg = ft.Container(expand=True, gradient=brand_gradient(),
                      bgcolor=_alpha(getattr(ft.colors, "ON_SURFACE", ft.colors.WHITE), 0.02))

    return ft.View(
        route="/",
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    bg,
                    ft.Container(expand=True, alignment=ft.alignment.center, content=form),
                ],
            )
        ],
    )
