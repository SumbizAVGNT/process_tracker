from __future__ import annotations
import flet as ft

from ...db.session import AsyncSessionLocal
from ...services.process_service import ProcessService
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..components.theme import card  # card(content)

def view(page: ft.Page) -> ft.View:
    title = ft.TextField(label="Название", hint_text="Коротко опишите задачу", expand=True, dense=True)
    desc = ft.TextField(label="Описание", hint_text="Детали…", multiline=True, min_lines=3, max_lines=6, expand=True, dense=True)
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
            await ProcessService(s).create(t, (desc.value or "").strip() or None, (status.value or "new"))
        toast(page, "Задача создана", kind="success")
        title.value, desc.value, status.value = "", "", "new"
        page.update()

    form_card = card(
        ft.Column(
            [
                ft.Text("Создать задачу", size=20, weight="w800"),
                ft.Container(height=10),
                ft.Row([title]),
                ft.Row([desc]),
                ft.Row(
                    [status, ft.Container(expand=True), async_button(page, "Сохранить", task_factory=submit, icon="SAVE")],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
            tight=True,
        )
    )

    form = ft.Container(content=form_card, padding=18)
    return page_scaffold(page, title="Создать задачу", route="/tasks/create", body=form)
