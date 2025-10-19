from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import toast, async_button
from ..auth import sign_in

def view(page: ft.Page) -> ft.View:
    email = ft.TextField(label="Email", hint_text="name@company.com", autofocus=True, dense=True, expand=True)
    roles = ft.TextField(label="Роли (через запятую)", hint_text="admin,manager", dense=True, expand=True)
    perms = ft.TextField(label="Права (через запятую)", hint_text="process.read,task.create", dense=True, expand=True)

    async def do_login():
        e = (email.value or "").strip()
        if not e:
            toast(page, "Введите email", kind="warning"); return
        r = [x.strip() for x in (roles.value or "").split(",") if x.strip()]
        p = [x.strip() for x in (perms.value or "").split(",") if x.strip()]
        await sign_in(e, roles=r, perms=p)
        page.go("/dashboard")

    btn = async_button(page, "Войти", task_factory=do_login, icon=ft.icons.LOGIN)

    form = ft.Column(
        [
            ft.Text("Вход", size=22, weight="w800"),
            ft.Text("DEV-login: укажи email (опционально роли/права)"),
            ft.Divider(opacity=0.06),
            email, roles, perms,
            ft.Container(height=8),
            ft.Row([btn], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=10,
        tight=True,
    )

    card = ft.Container(
        content=form,
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE),
        width=520,
    )

    # ВАЖНО: не expand! Просто колонка, дальше её центрирует каркас.
    body = ft.Column([card])

    return page_scaffold(page, title="Вход", route="/", body=body, show_topbar=False, show_nav=False, center=True)
