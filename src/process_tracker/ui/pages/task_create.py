from __future__ import annotations
import flet as ft
from ...db.session import AsyncSessionLocal
from ...services.process_service import ProcessService
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast

def view(page: ft.Page) -> ft.View:
    title = ft.TextField(label="Название", hint_text="Коротко опишите задачу", expand=True)
    desc = ft.TextField(label="Описание", hint_text="Детали…", multiline=True, min_lines=3, max_lines=6, expand=True)
    status = ft.Dropdown(
        label="Статус",
        options=[ft.dropdown.Option("new"), ft.dropdown.Option("in_progress"), ft.dropdown.Option("done")],
        value="new",
        width=220,
    )

    async def submit():
        t = (title.value or "").strip()
        if not t:
            toast(page, "Название обязательно", kind="warning"); return
        async with AsyncSessionLocal() as s:
            svc = ProcessService(s)
            await svc.create(t, (desc.value or "").strip() or None, (status.value or "new"))
        toast(page, "Задача создана", kind="success")
        title.value, desc.value, status.value = "", "", "new"
        page.update()

    body = ft.Column(
        [
            ft.Text("Создать задачу", size=18, weight="w800"),
            ft.Container(height=10),
            ft.Row([title], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([desc], vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row(
                [
                    status,
                    ft.Container(expand=True),
                    async_button(page, "Сохранить", task_factory=submit, icon=ft.icons.SAVE),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=10,
        tight=True,
    )
    return page_scaffold(page, title="Создать задачу", route="/tasks/create", body=body)
