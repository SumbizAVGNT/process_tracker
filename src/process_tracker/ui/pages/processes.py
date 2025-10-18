from __future__ import annotations

import flet as ft

from ..components.navbar import navbar
from ..components.forms import task_editor, confirm_dialog, toast
from ...db.session import AsyncSessionLocal
from ...services.task_service import TaskService
from ...core.events import events


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — задачи"

    title = ft.Text("Задачи", size=24, weight="bold")
    subtitle = ft.Text(
        "Создавай, отмечай выполненные и удаляй — всё обновляется live.",
        color=ft.colors.ON_SURFACE_VARIANT,
    )

    list_view = ft.ListView(expand=1, spacing=6, padding=6, auto_scroll=False)

    async def add_task_handler(name: str):
        name = (name or "").strip()
        if not name:
            toast(page, "Введите название задачи", kind="warn")
            return
        async with AsyncSessionLocal() as s:
            await TaskService(s).create(name)

    editor = task_editor(page, on_save=add_task_handler, label="Новая задача", button_text="Добавить")

    def _task_row(task_id: int, title: str, done: bool) -> ft.Row:
        checkbox = ft.Checkbox(value=done, label=f"#{task_id}  {title}", expand=True)
        delete_btn = ft.IconButton(icon=ft.icons.DELETE_OUTLINE, tooltip="Удалить")

        async def toggle_done(_event):
            async with AsyncSessionLocal() as s:
                ok = await TaskService(s).set_done(task_id, checkbox.value)
            if not ok:
                toast(page, "Задача не найдена (возможно, уже удалена)", kind="warn")

        async def delete_task(_event):
            if await confirm_dialog(page, title="Удалить задачу", text=f"Удалить «{title}»?"):
                async with AsyncSessionLocal() as s:
                    removed = await TaskService(s).remove(task_id)
                if not removed:
                    toast(page, "Задача не найдена (возможно, уже удалена)", kind="warn")

        # ВАЖНО: передаём функцию, а не вызов
        checkbox.on_change = lambda e: page.run_task(toggle_done, e)
        delete_btn.on_click = lambda e: page.run_task(delete_task, e)

        return ft.Row([checkbox, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    async def load_tasks(_event=None):
        async with AsyncSessionLocal() as s:
            tasks = await TaskService(s).list()
        list_view.controls = [_task_row(t.id, t.title, t.done) for t in tasks]
        page.update()

    async def watch_events():
        q = await events.subscribe()
        try:
            while True:
                ev = await q.get()
                if isinstance(ev, dict) and str(ev.get("type", "")).startswith("task_"):
                    await load_tasks()
        finally:
            await events.unsubscribe(q)

    # первичная загрузка и подписка (ВАЖНО: функции, без скобок)
    page.run_task(load_tasks)
    page.run_task(watch_events)

    content = ft.Column(
        [
            ft.Row([title], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            subtitle,
            ft.Divider(height=12, color="transparent"),
            editor,
            ft.Container(list_view, expand=True),
        ],
        expand=True,
        spacing=10,
    )

    return ft.View(
        route="/processes",
        controls=[
            navbar(page),
            ft.Container(content=content, padding=ft.padding.symmetric(16, 18), expand=True),
        ],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
