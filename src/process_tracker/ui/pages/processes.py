from __future__ import annotations
import flet as ft
from typing import List
from ...db.session import AsyncSessionLocal
from ...services.process_service import ProcessService
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast

async def _load() -> List:
    async with AsyncSessionLocal() as s:
        return await ProcessService(s).get_recent(limit=100)

def view(page: ft.Page) -> ft.View:
    table = ft.Column(spacing=6, tight=True)

    async def refresh():
        items = await _load()
        rows: list[ft.Control] = []
        for it in items:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"#{getattr(it, 'id', '-')}", width=60),
                            ft.Text(getattr(it, "title", "(без названия)"), expand=True),
                            ft.Text(getattr(it, "status", "new"), width=100),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE)),
                    border_radius=10,
                )
            )
        table.controls = rows or [ft.Text("Пока нет процессов…", color=ft.colors.ON_SURFACE_VARIANT)]
        try: page.update()
        except Exception: pass

    page.run_task(refresh)

    body = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Процессы", size=18, weight="w800"),
                    ft.Container(expand=True),
                    async_button(page, "Обновить", task_factory=refresh, icon=ft.icons.REFRESH),
                    ft.FilledButton("Создать задачу", icon=ft.icons.ADD, on_click=lambda _: page.go("/tasks/create")),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=10),
            table,
        ],
        spacing=0,
        tight=True,
    )
    return page_scaffold(page, title="Процессы", route="/processes", body=body)
