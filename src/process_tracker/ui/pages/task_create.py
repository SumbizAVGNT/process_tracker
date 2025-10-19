from __future__ import annotations
import flet as ft

from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..services.api import api

def view(page: ft.Page) -> ft.View:
    title = ft.TextField(label="Название задачи", hint_text="Короткое описание…", expand=True, dense=True)

    async def save():
        t = (title.value or "").strip()
        if not t:
            toast(page, "Введите название", kind="warning"); return
        try:
            await api.create_task(t)
            toast(page, "Задача создана", kind="success")
            page.go("/dashboard")
        except Exception as ex:  # noqa: BLE001
            toast(page, f"Ошибка: {ex}", kind="error")

    btn = async_button(page, "Создать", task_factory=save, icon=ft.icons.CHECK)

    body = ft.Column(
        [
            ft.Text("Создать задачу", size=20, weight="w800"),
            ft.Divider(opacity=0.06),
            title,
            ft.Container(height=8),
            ft.Row([btn], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=10,
        tight=True,
    )
    return page_scaffold(page, title="Создать задачу", route="/tasks/create", body=body)
