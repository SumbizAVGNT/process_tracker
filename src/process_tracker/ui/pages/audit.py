from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button
from ..components.filters_bar import filters_bar
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Аудит", size=22, weight="w700")
    entity = ft.Dropdown(label="Сущность", options=[ft.dropdown.Option("task"), ft.dropdown.Option("process")], dense=True, value=None)
    entity_id = ft.TextField(label="ID", dense=True, width=120)
    event = ft.TextField(label="Событие", dense=True, width=180)
    list_view = ft.ListView(expand=True, spacing=6, padding=0)

    async def load():
        ent_id = int(entity_id.value) if (entity_id.value or "").strip().isdigit() else None
        items = await api.audit_list(entity.value, ent_id, (event.value or None))
        list_view.controls = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(it["ts"].replace("T", " ").replace("Z", ""), size=12, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Text(f"{it['entity']}#{it['entity_id']} • {it['event']}"),
                    ],
                    spacing=10,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.WHITE)),
                border_radius=10,
            )
            for it in items
        ]
        page.update()

    body = ft.Column(
        [
            title,
            filters_bar(entity, entity_id, event, async_button(page, "Обновить", icon=ft.icons.REFRESH, task_factory=load)),
            list_view,
        ],
        spacing=10,
        expand=True,
    )

    page.run_task(load)
    return page_scaffold(page, title="Аудит", route="/audit", body=body)
