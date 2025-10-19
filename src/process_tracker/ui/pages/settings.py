from __future__ import annotations
import flet as ft
from sqlalchemy import text
from ...db.session import AsyncSessionLocal
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast

def view(page: ft.Page) -> ft.View:
    db_url = ft.TextField(label="Строка подключения (readonly)", value="(см. .env)", read_only=True, expand=True)

    async def test_db():
        try:
            async with AsyncSessionLocal() as s:
                res = await s.execute(text("SELECT 1"))
                ok = bool(res.scalar())
            toast(page, "БД доступна" if ok else "Нет ответа", kind="success" if ok else "error")
        except Exception as e:
            toast(page, f"Ошибка БД: {e}", kind="error")

    body = ft.Column(
        [
            ft.Text("Настройки", size=18, weight="w800"),
            ft.Container(height=10),
            ft.Row([db_url], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=6),
            ft.Row(
                [
                    async_button(page, "Проверить БД", task_factory=test_db, icon=ft.icons.STORAGE if hasattr(ft.icons, "STORAGE") else ft.icons.SETTINGS),
                    ft.OutlinedButton("Открыть процессы", icon=ft.icons.LIST, on_click=lambda _: page.go("/processes")),
                    ft.OutlinedButton("На дашборд", icon=ft.icons.DASHBOARD, on_click=lambda _: page.go("/dashboard")),
                ],
                spacing=10,
            ),
        ],
        spacing=10,
        tight=True,
    )
    return page_scaffold(page, title="Настройки", route="/settings", body=body)
