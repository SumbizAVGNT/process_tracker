from __future__ import annotations
import flet as ft

from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..services.api import api

def view(page: ft.Page) -> ft.View:
    table = ft.Column(spacing=6, tight=True)

    async def load():
        try:
            items = await api.list_processes(limit=100)
        except Exception as ex:  # noqa: BLE001
            toast(page, f"Ошибка загрузки: {ex}", kind="error")
            return
        table.controls[:] = []
        for p in items:
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(f"#{p['id']}", width=60),
                        ft.Text(p["name"], expand=True),
                        ft.Container(width=10),
                        ft.Chip(label=ft.Text(p["status"])),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                border_radius=10,
                bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE),
            )
            table.controls.append(row)
        page.update()

    name = ft.TextField(label="Новый процесс", hint_text="Название…", dense=True, expand=True)

    async def add():
        n = (name.value or "").strip()
        if not n:
            toast(page, "Введите название", kind="warning"); return
        await api.create_process(n)
        name.value = ""
        await load()

    add_btn = async_button(page, "Добавить", task_factory=add, icon=ft.icons.ADD)

    header = ft.Row([ft.Text("Процессы", size=20, weight="w800")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    toolbar = ft.Row([name, add_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.END)

    body = ft.Column([header, ft.Container(height=8), toolbar, ft.Container(height=8), table], spacing=0, tight=True)

    try:
        page.run_task(load)
    except Exception:
        pass

    return page_scaffold(page, title="Процессы", route="/processes", body=body)
