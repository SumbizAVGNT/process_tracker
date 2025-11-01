from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..components.empty_state import empty_state
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Представления", size=22, weight="w700")
    list_view = ft.ListView(expand=True, spacing=8, padding=0)

    async def load():
        items = await api.views_list()
        if not items:
            list_view.controls = [empty_state("Нет сохранённых представлений", "Создайте новое", action=_create_btn())]
        else:
            list_view.controls = [
                ft.Card(
                    content=ft.ListTile(
                        title=ft.Text(v["name"]),
                        subtitle=ft.Text(f"{v['resource']} • {v['layout']}"),
                        trailing=ft.Row(
                            [
                                ft.IconButton(
                                    ft.icons.EDIT,
                                    on_click=lambda _e, data=v: page.run_task(lambda: edit_dialog(data)),
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE_OUTLINE,
                                    on_click=lambda _e, _id=v["id"]: page.run_task(lambda: delete(_id)),
                                ),
                            ],
                            spacing=4,
                        ),
                        dense=True,
                    )
                )
                for v in items
            ]
        page.update()

    def _create_btn():
        return async_button(page, "Создать", icon=ft.icons.ADD, task_factory=lambda: edit_dialog(None))

    async def edit_dialog(v: dict | None):
        name = ft.TextField(label="Название", value=(v or {}).get("name", ""), dense=True)
        resource = ft.Dropdown(
            label="Ресурс",
            options=[ft.dropdown.Option("tasks"), ft.dropdown.Option("processes")],
            value=(v or {}).get("resource", "tasks"),
            dense=True,
        )
        layout = ft.Dropdown(
            label="Вид",
            options=[ft.dropdown.Option(x) for x in ["list", "kanban", "calendar", "gantt"]],
            value=(v or {}).get("layout", "list"),
            dense=True,
        )
        query = ft.TextField(
            label="Фильтры (JSON)", value=_fmt_json((v or {}).get("query")),
            dense=True, multiline=True, min_lines=3, max_lines=8
        )
        meta = ft.TextField(
            label="Meta (JSON)", value=_fmt_json((v or {}).get("meta")),
            dense=True, multiline=True, min_lines=3, max_lines=8
        )
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Представление"))

        async def _save():
            payload = {
                "name": name.value.strip(),
                "resource": resource.value,
                "layout": layout.value,
                "query": _parse_json(query.value) or {},
                "meta": _parse_json(meta.value) or {},
            }
            if v and v.get("id"):
                await api.views_patch(int(v["id"]), payload)
            else:
                await api.views_create(payload)
            toast(page, "Сохранено", kind="success")
            dlg.open = False
            page.update()
            await load()

        dlg.content = ft.Container(ft.Column([name, resource, layout, query, meta], tight=True, spacing=10), width=640)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=lambda _e: _close(dlg)),
            async_button(page, "Сохранить", icon=ft.icons.CHECK, task_factory=_save),
        ]
        page.dialog = dlg
        dlg.open = True
        page.update()

    def _fmt_json(obj):
        import json
        if not obj:
            return ""
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)

    def _parse_json(s: str):
        import json
        s = (s or "").strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}

    def _close(dlg: ft.AlertDialog):
        dlg.open = False
        page.update()

    async def delete(view_id: int):
        await api.views_delete(view_id)
        await load()

    body = ft.Column([title, _create_btn(), list_view], spacing=10, expand=True)
    page.run_task(load)
    return page_scaffold(page, title="Представления", route="/views", body=body)
