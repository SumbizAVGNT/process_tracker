from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..components.empty_state import empty_state
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Пользователи", size=22, weight="w700")
    list_view = ft.ListView(expand=True, spacing=8, padding=0)

    async def load():
        users = await api.users_list()
        if not users:
            list_view.controls = [empty_state("Пользователей нет", "Создайте пользователя", action=_create_btn())]
        else:
            list_view.controls = [
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                        title=ft.Text(u["email"]),
                        subtitle=ft.Text(
                            (u.get("name") or "-") + ("  •  inactive" if not u.get("is_active", True) else "")
                        ),
                        trailing=ft.Row(
                            [
                                ft.IconButton(
                                    ft.icons.EDIT, tooltip="Редактировать",
                                    on_click=lambda _e, data=u: page.run_task(lambda: edit_dialog(data))
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE_OUTLINE, tooltip="Удалить",
                                    on_click=lambda _e, _id=u["id"]: page.run_task(lambda: delete(_id))
                                ),
                            ],
                            spacing=4,
                        ),
                        dense=True,
                    )
                )
                for u in users
            ]
        page.update()

    def _create_btn():
        return async_button(page, "Создать", icon=ft.icons.ADD, task_factory=lambda: edit_dialog(None))

    async def edit_dialog(user: dict | None):
        email = ft.TextField(label="Email", value=(user or {}).get("email", ""), dense=True)
        name = ft.TextField(label="Имя", value=(user or {}).get("name", ""), dense=True)
        active = ft.Switch(label="Активен", value=(user or {}).get("is_active", True))
        roles = ft.TextField(label="Роли (через запятую)", value=",".join((user or {}).get("roles", [])), dense=True)
        perms = ft.TextField(label="Права (через запятую)", value=",".join((user or {}).get("perms", [])), dense=True)
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Пользователь"))

        async def _save():
            payload = {
                "email": email.value.strip(),
                "name": (name.value or None),
                "is_active": bool(active.value),
                "roles": [x.strip() for x in (roles.value or "").split(",") if x.strip()],
                "perms": [x.strip() for x in (perms.value or "").split(",") if x.strip()],
            }
            if user and user.get("id"):
                await api.users_patch(int(user["id"]), payload)
            else:
                await api.users_create(payload)
            toast(page, "Сохранено", kind="success")
            dlg.open = False
            page.update()
            await load()

        dlg.content = ft.Container(ft.Column([email, name, active, roles, perms], tight=True, spacing=10), width=520)
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

    async def delete(user_id: int):
        await api.users_delete(user_id)
        await load()

    body = ft.Column([title, _create_btn(), list_view], spacing=10, expand=True)
    page.run_task(load)
    return page_scaffold(page, title="Пользователи", route="/users", body=body)
