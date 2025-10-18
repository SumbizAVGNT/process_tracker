# src/process_tracker/ui/pages/dashboard.py

from __future__ import annotations

import flet as ft

from ..components.navbar import navbar
from ...db.session import AsyncSessionLocal
from ...services.task_service import TaskService
from ...services.process_service import ProcessService
from ..components.forms import toast


def _stat_card(title: str, value_ref: ft.Text, icon: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=36),
                ft.Column(
                    [
                        ft.Text(title, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                        value_ref,
                    ],
                    spacing=4,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=16,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE_VARIANT),
    )


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — дашборд"

    # Заголовок и действия
    title = ft.Text("Дашборд", size=24, weight="bold")
    subtitle = ft.Text(
        "Сводка по процессам и задачам",
        color=ft.colors.ON_SURFACE_VARIANT,
    )
    go_tasks_btn = ft.FilledButton(
        "Перейти к задачам",
        icon=ft.icons.CHECKLIST,
        on_click=lambda _: page.go("/processes"),
    )

    # Метрики
    tasks_total_val = ft.Text("—", size=20, weight="bold")
    tasks_open_val = ft.Text("—", size=20, weight="bold")
    processes_total_val = ft.Text("—", size=20, weight="bold")

    stat_tasks_total = _stat_card("Всего задач", tasks_total_val, ft.icons.LIST_ALT_OUTLINED)
    stat_tasks_open = _stat_card("Открытые задачи", tasks_open_val, ft.icons.PENDING_ACTION)
    stat_processes_total = _stat_card("Всего процессов", processes_total_val, ft.icons.DASHBOARD_OUTLINED)

    grid = ft.ResponsiveRow(
        controls=[
            ft.Container(stat_tasks_total, col={"xs": 12, "md": 4}),
            ft.Container(stat_tasks_open, col={"xs": 12, "md": 4}),
            ft.Container(stat_processes_total, col={"xs": 12, "md": 4}),
        ],
        columns=12,
        run_spacing=12,
    )

    # Последние действия / placeholder
    activity = ft.Container(
        content=ft.Column(
            [
                ft.Text("Активность", size=16, weight="bold"),
                ft.Text("Скоро здесь будет лента событий (создание/обновление задач и процессов)…",
                        color=ft.colors.ON_SURFACE_VARIANT),
            ],
            spacing=8,
        ),
        padding=16,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.03, ft.colors.SURFACE_VARIANT),
    )

    async def load_stats():
        try:
            async with AsyncSessionLocal() as s:
                tsvc = TaskService(s)
                psvc = ProcessService(s)
                tasks = await tsvc.list()
                processes = await psvc.get_recent()

            total = len(tasks)
            open_ = sum(1 for t in tasks if not t.done)
            ptotal = len(processes)

            tasks_total_val.value = str(total)
            tasks_open_val.value = str(open_)
            processes_total_val.value = str(ptotal)

            page.update()
        except Exception as e:  # noqa: BLE001
            toast(page, f"Не удалось загрузить статистику: {e}", kind="error")

    # первичная загрузка
    page.run_task(load_stats())

    return ft.View(
        route="/dashboard",
        controls=[
            navbar(page),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([title, go_tasks_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        subtitle,
                        ft.Divider(height=14, color="transparent"),
                        grid,
                        ft.Divider(height=14, color="transparent"),
                        activity,
                    ],
                    spacing=10,
                ),
                padding=ft.padding.symmetric(16, 18),
                expand=True,
            ),
        ],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
