from __future__ import annotations
import flet as ft
from typing import List
from sqlalchemy import select, desc
from ...db.session import AsyncSessionLocal
from ...db.models import Process
from ...services.process_service import ProcessService
from ..components.forms import task_editor, confirm_dialog, toast, async_button
from ..components.navbar import navbar

def _tile(page: ft.Page, item: Process, on_delete) -> ft.ListTile:
    subt = (item.description or "").strip() or "—"
    return ft.ListTile(
        leading=ft.Icon(ft.icons.TASK_ALT_OUTLINED),
        title=ft.Text(item.title, weight="w600"),
        subtitle=ft.Text(f"{subt}  •  статус: {getattr(item, 'status', 'new')}"),
        trailing=ft.IconButton(
            icon=ft.icons.DELETE_OUTLINE, tooltip="Удалить",
            on_click=lambda _e, pid=item.id: on_delete(pid),
        ),
        data=item.id,
    )

def view(page: ft.Page) -> ft.View:
    page.title = "Процессы — Process Tracker"

    lst = ft.ListView(expand=True, spacing=4, padding=0, auto_scroll=False)

    async def refresh():
        lst.controls.clear()
        async with AsyncSessionLocal() as s:
            svc = ProcessService(s)
            items: List[Process] = await svc.get_recent(limit=100)
        for it in items:
            lst.controls.append(_tile(page, it, on_delete))
        try:
            lst.update()
        except Exception:
            pass

    async def add_process(title: str):
        t = (title or "").strip()
        if not t:
            toast(page, "Название не должно быть пустым", kind="warning")
            return
        async with AsyncSessionLocal() as s:
            svc = ProcessService(s)
            await svc.create(t, description=None, status="new")
        await refresh()
        toast(page, "Процесс создан", kind="success")

    async def on_delete(pid: int):
        if not await confirm_dialog(page, text="Удалить процесс?", ok_text="Удалить"):
            return
        async with AsyncSessionLocal() as s:
            obj = await s.get(Process, pid)
            if obj:
                await s.delete(obj)
                await s.commit()
        await refresh()
        toast(page, "Удалено", kind="success")

    header = ft.Row(
        [
            ft.Text("Процессы", size=18, weight="w700"),
            ft.Container(expand=1),
            async_button(page, "Обновить", task_factory=refresh, icon=ft.icons.REFRESH),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body = ft.Column(
        [
            navbar(page, "/processes"),
            ft.Container(height=8),
            header,
            ft.Container(height=6),
            task_editor(page, on_save=add_process, label="Новый процесс", button_text="Добавить"),
            ft.Container(height=10),
            lst,
        ],
        expand=True, spacing=10,
    )

    # первичная загрузка
    page.run_task(refresh)

    return ft.View(route="/processes", controls=[ft.Container(content=body, expand=True, padding=16)])
