from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..components.empty_state import empty_state
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Вебхуки", size=22, weight="w700")
    list_view = ft.ListView(expand=True, spacing=8, padding=0)

    async def load():
        hooks = await api.webhooks_list()
        if not hooks:
            list_view.controls = [empty_state("Нет вебхуков", "Добавьте первый", action=_create_btn())]
        else:
            list_view.controls = [
                ft.Card(
                    content=ft.ListTile(
                        title=ft.Text(h["url"]),
                        subtitle=ft.Text(", ".join(h.get("events", ["*"]))),
                        leading=ft.Icon(ft.icons.CLOUD_OUTLINED),
                        trailing=ft.Row(
                            [
                                ft.Switch(
                                    value=bool(h.get("is_active", True)),
                                    on_change=lambda e, _id=h["id"]: page.run_task(
                                        lambda: toggle(_id, e.control.value)
                                    ),
                                ),
                                ft.IconButton(
                                    ft.icons.SEND, tooltip="Тест",
                                    on_click=lambda _e, _id=h["id"]: page.run_task(lambda: test(_id))
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE_OUTLINE, tooltip="Удалить",
                                    on_click=lambda _e, _id=h["id"]: page.run_task(lambda: delete(_id))
                                ),
                            ],
                            spacing=4,
                        ),
                        dense=True,
                    ),
                )
                for h in hooks
            ]
        page.update()

    def _create_btn() -> ft.Control:
        return async_button(page, "Добавить", icon=ft.icons.ADD, task_factory=lambda: create_dialog())

    async def create_dialog():
        url = ft.TextField(label="URL", hint_text="https://example.com/hook", dense=True)
        events = ft.TextField(label="События (через запятую)", value="*", dense=True)
        secret = ft.TextField(label="Секрет (опционально)", dense=True)
        active = ft.Switch(label="Активен", value=True)
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Новый вебхук"))

        async def _save():
            payload = {
                "url": url.value.strip(),
                "events": [x.strip() for x in (events.value or "*").split(",") if x.strip()],
                "secret": (secret.value or None),
                "is_active": bool(active.value),
            }
            await api.webhooks_create(payload)
            toast(page, "Создано", kind="success")
            dlg.open = False
            page.update()
            await load()

        dlg.content = ft.Container(ft.Column([url, events, secret, active], tight=True, spacing=10), width=520)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=lambda _e: _close(dlg)),
            async_button(page, "Сохранить", icon=ft.icons.CHECK, task_factory=_save),
        ]
        page.dialog = dlg
        dlg.open = True
        page.update()

    def _close(d: ft.AlertDialog):
        d.open = False
        page.update()

    async def toggle(hook_id: int, active: bool):
        await api.webhooks_patch(hook_id, {"is_active": active})
        await load()

    async def test(hook_id: int):
        await api.webhooks_test(hook_id, "test.ping", {"hello": "world"})
        toast(page, "Отправлено", kind="success")

    async def delete(hook_id: int):
        await api.webhooks_delete(hook_id)
        await load()

    body = ft.Column([title, _create_btn(), list_view], spacing=10, expand=True)
    page.run_task(load)
    return page_scaffold(page, title="Вебхуки", route="/webhooks", body=body)
