from __future__ import annotations
from typing import Any
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..components.filters_bar import filters_bar
from ..components.empty_state import empty_state
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Шаблоны", size=22, weight="w700")
    search = ft.TextField(prefix_icon=ft.icons.SEARCH, hint_text="Поиск по ключу/названию…", dense=True, expand=True)
    list_view = ft.ListView(expand=True, spacing=8, padding=0)

    async def load():
        q = (search.value or None)
        items = await api.templates_list(q=q)
        if not items:
            list_view.controls = [empty_state("Пусто", "Создайте первый шаблон", action=_create_btn())]
        else:
            list_view.controls = [
                ft.Card(
                    content=ft.ListTile(
                        title=ft.Text(f"{it['title']}"),
                        subtitle=ft.Text(it["key"]),
                        trailing=ft.Row(
                            [
                                ft.IconButton(
                                    ft.icons.EDIT, tooltip="Редактировать",
                                    on_click=lambda _e, _id=it["id"]: page.run_task(lambda: edit_dialog(_id, it))
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE_OUTLINE, tooltip="Удалить",
                                    on_click=lambda _e, _id=it["id"]: page.run_task(lambda: delete_item(_id))
                                ),
                            ],
                            spacing=4,
                        ),
                        on_click=lambda _e, data=it: page.run_task(lambda: edit_dialog(data["id"], data)),
                        dense=True,
                    ),
                )
                for it in items
            ]
        page.update()

    def _create_btn() -> ft.Control:
        return async_button(page, "Создать", icon=ft.icons.ADD, task_factory=lambda: create_dialog())

    async def create_dialog():
        await _template_dialog()
        await load()

    async def edit_dialog(tid: int, data: dict):
        await _template_dialog(data)
        await load()

    async def delete_item(tid: int):
        try:
            await api.templates_delete(tid)
            toast(page, "Удалено", kind="success")
            await load()
        except Exception as e:
            toast(page, str(e), kind="error")

    async def _template_dialog(data: dict | None = None):
        key = ft.TextField(label="Ключ", value=(data or {}).get("key", ""), dense=True)
        title_f = ft.TextField(label="Название", value=(data or {}).get("title", ""), dense=True)
        visibility = ft.Dropdown(
            label="Доступ",
            options=[ft.dropdown.Option("private"), ft.dropdown.Option("org"), ft.dropdown.Option("public")],
            value=(data or {}).get("visibility", "private"),
            dense=True,
        )
        form_schema = ft.TextField(
            label="form_schema (JSON)", value=_fmt_json((data or {}).get("form_schema")),
            dense=True, multiline=True, min_lines=4, max_lines=10
        )
        workflow_def = ft.TextField(
            label="workflow_def (JSON)", value=_fmt_json((data or {}).get("workflow_def")),
            dense=True, multiline=True, min_lines=4, max_lines=10
        )

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Шаблон"), actions_alignment=ft.MainAxisAlignment.END)

        async def _save():
            payload = {
                "key": key.value.strip(),
                "title": title_f.value.strip(),
                "visibility": visibility.value,
                "form_schema": _parse_json(form_schema.value),
                "workflow_def": _parse_json(workflow_def.value),
            }
            try:
                if data and data.get("id"):
                    await api.templates_patch(int(data["id"]), payload)
                else:
                    await api.templates_create(payload)
                toast(page, "Сохранено", kind="success")
                dlg.open = False
                page.update()
            except Exception as e:
                toast(page, str(e), kind="error")

        dlg.content = ft.Container(
            ft.Column([key, title_f, visibility, form_schema, workflow_def], tight=True, spacing=10), width=640
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=lambda _e: _close(dlg)),
            async_button(page, "Сохранить", task_factory=_save, icon=ft.icons.CHECK),
        ]
        page.dialog = dlg
        dlg.open = True
        page.update()

    def _close(d: ft.AlertDialog):
        d.open = False
        page.update()

    def _fmt_json(obj: Any) -> str:
        import json
        if not obj:
            return ""
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)

    def _parse_json(s: str) -> Any:
        import json
        s = (s or "").strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except Exception:
            return None

    search.on_submit = lambda _e: page.run_task(load)
    header = filters_bar(search, _create_btn())
    body = ft.Column([header, list_view], spacing=10, expand=True)
    page.run_task(load)
    return page_scaffold(page, title="Шаблоны", route="/templates", body=body)
