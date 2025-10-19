from __future__ import annotations
import flet as ft
from sqlalchemy import select, func
from ...db.session import AsyncSessionLocal
from ...db.models import Task, Process
from ..components.shell import page_scaffold
from ..components.theme import kpi

async def _load_counts():
    open_cnt = 0
    done_cnt = 0
    proc_cnt = 0
    async with AsyncSessionLocal() as s:
        # Всего процессов
        try:
            proc_cnt = (await s.scalar(select(func.count()).select_from(Process))) or 0
        except Exception:
            proc_cnt = 0
        # Всего задач
        try:
            total = (await s.scalar(select(func.count()).select_from(Task))) or 0
        except Exception:
            total = 0
        # Если есть поле status — посчитаем done/open, иначе всё в "открытые"
        try:
            if hasattr(Task, "status"):
                done_cnt = (await s.scalar(select(func.count()).select_from(Task).where(Task.status == "done"))) or 0
                open_cnt = max(total - done_cnt, 0)
            else:
                open_cnt = total
        except Exception:
            open_cnt = total
            done_cnt = 0
    return open_cnt, done_cnt, proc_cnt

def view(page: ft.Page) -> ft.View:
    v_open, v_done, v_proc = ft.Text("0", size=22, weight="w800"), ft.Text("0", size=22, weight="w800"), ft.Text("0", size=22, weight="w800")

    async def refresh():
        o, d, p = await _load_counts()
        v_open.value, v_done.value, v_proc.value = str(o), str(d), str(p)
        try: page.update()
        except Exception: pass

    page.run_task(refresh)

    grid = ft.Row(
        [
            kpi("Открытые задачи", v_open, icon=ft.icons.LOCAL_FIRE_DEPARTMENT if hasattr(ft.icons, "LOCAL_FIRE_DEPARTMENT") else ft.icons.WHATSHOT),
            kpi("Завершено задач", v_done, icon=ft.icons.CHECK_CIRCLE_OUTLINE if hasattr(ft.icons, "CHECK_CIRCLE_OUTLINE") else ft.icons.CHECK_CIRCLE),
            kpi("Всего процессов", v_proc, icon=ft.icons.WORKSPACES_OUTLINED if hasattr(ft.icons, "WORKSPACES_OUTLINED") else ft.icons.WORK),
        ],
        spacing=16,
        run_spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    actions = ft.Row(
        [
            ft.FilledButton("Создать задачу", icon=ft.icons.ADD, on_click=lambda _: page.go("/tasks/create")),
            ft.OutlinedButton("К процессам", icon=ft.icons.LIST, on_click=lambda _: page.go("/processes")),
            ft.OutlinedButton("Настройки", icon=ft.icons.SETTINGS, on_click=lambda _: page.go("/settings")),
        ],
        spacing=10,
    )

    body = ft.Column(
        [
            ft.Text("Обзор", size=18, weight="w800"),
            ft.Container(height=10),
            grid,
            ft.Container(height=12),
            actions,
        ],
        spacing=0,
        tight=True,
    )

    return page_scaffold(page, title="Дашборд", route="/dashboard", body=body)
