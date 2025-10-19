from __future__ import annotations
import flet as ft
from ..components.navbar import navbar
from ..components.forms import async_button, toast

# Опционально попробуем сервис
try:
    from ...services.workflow_service import WorkflowService  # type: ignore
    from ...db.session import AsyncSessionLocal
except Exception:
    WorkflowService = None  # type: ignore

def view(page: ft.Page) -> ft.View:
    page.title = "Воркфлоу — Process Tracker"
    lst = ft.ListView(expand=True, spacing=4, padding=0)

    async def refresh():
        lst.controls.clear()
        if not WorkflowService:
            lst.controls.append(ft.ListTile(
                leading=ft.Icon(ft.icons.INFO),
                title=ft.Text("Воркфлоу пока как заглушка"),
                subtitle=ft.Text("Подключим к API/БД — и здесь появится список."),
            ))
        else:
            async with AsyncSessionLocal() as s:
                svc = WorkflowService(s)
                items = await svc.get_recent()  # если есть
            if not items:
                lst.controls.append(ft.ListTile(title=ft.Text("Пока пусто")))
            else:
                for wf in items:
                    lst.controls.append(ft.ListTile(
                        leading=ft.Icon(ft.icons.ROCKET_LAUNCH),
                        title=ft.Text(getattr(wf, "name", f"WF #{getattr(wf, 'id', '?')}")),
                        subtitle=ft.Text(getattr(wf, "description", "—")),
                    ))
        try:
            lst.update()
        except Exception:
            pass

    body = ft.Column(
        [
            navbar(page, "/workflows"),
            ft.Container(height=8),
            ft.Row([
                ft.Text("Воркфлоу", size=18, weight="w700"),
                ft.Container(expand=1),
                async_button(page, "Обновить", task_factory=refresh, icon=ft.icons.REFRESH),
            ]),
            ft.Container(height=8),
            lst,
        ],
        expand=True, spacing=10,
    )

    page.run_task(refresh)
    return ft.View(route="/workflows", controls=[ft.Container(content=body, expand=True, padding=16)])
