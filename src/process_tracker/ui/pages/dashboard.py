from __future__ import annotations

import flet as ft
from sqlalchemy import select, func

from ...db.session import AsyncSessionLocal
from ...db.models import Task, Process  # используем модели напрямую
from ..components.navbar import navbar


CARD_PAD = 14
CARD_RADIUS = 16


async def _safe_count(session, model, *, where_clause=None) -> int:
    q = select(func.count()).select_from(model)
    if where_clause is not None:
        q = q.where(where_clause)
    return int(await session.scalar(q) or 0)


async def _count_open_tasks(session) -> int:
    cols = Task.__table__.c  # ColumnCollection
    if "status" in cols.keys():
        return await _safe_count(session, Task, where_clause=(cols.status != "done"))
    if "completed_at" in cols.keys():
        return await _safe_count(session, Task, where_clause=(cols.completed_at.is_(None)))
    # фолбэк — считаем все как «открытые»
    return await _safe_count(session, Task)


async def _count_done_tasks(session) -> int:
    cols = Task.__table__.c
    if "status" in cols.keys():
        return await _safe_count(session, Task, where_clause=(cols.status == "done"))
    if "completed_at" in cols.keys():
        return await _safe_count(session, Task, where_clause=(cols.completed_at.is_not(None)))
    # фолбэк — 0 «выполненных», если схемы нет
    return 0


def _stat_card(title: str, value: int, icon: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, size=22),
                    width=40,
                    height=40,
                    border_radius=12,
                    bgcolor=ft.colors.with_opacity(0.08, ft.colors.PRIMARY),
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text(title, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Text(str(value), size=22, weight="w700"),
                    ],
                    spacing=4,
                    tight=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=CARD_PAD,
        border_radius=CARD_RADIUS,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )


def view(page: ft.Page) -> ft.View:
    page.title = "Дашборд — Процесс Трекер"

    # начальные значения
    tasks_open_val = ft.Text("—", size=22, weight="w700")
    tasks_done_val = ft.Text("—", size=22, weight="w700")
    procs_total_val = ft.Text("—", size=22, weight="w700")

    async def load_stats():
        async with AsyncSessionLocal() as s:
            # процессы
            procs_total = await _safe_count(s, Process)
            # задачи
            open_count = await _count_open_tasks(s)
            done_count = await _count_done_tasks(s)

        tasks_open_val.value = str(open_count)
        tasks_done_val.value = str(done_count)
        procs_total_val.value = str(procs_total)
        try:
            tasks_open_val.update()
            tasks_done_val.update()
            procs_total_val.update()
        except Exception:
            pass

    # запускаем загрузку асинхронно (через Flet API)
    if hasattr(page, "run_task"):
        page.run_task(load_stats)
    else:
        # на всякий случай
        import asyncio
        try:
            asyncio.get_running_loop().create_task(load_stats())
        except RuntimeError:
            asyncio.run(load_stats())

    # карточки со статами
    ic = ft.icons
    stat_tasks_open = ft.Container(
        content=ft.Column(
            [ft.Text("Открытые задачи", size=12, color=ft.colors.ON_SURFACE_VARIANT), tasks_open_val],
            spacing=4,
            tight=True,
        ),
        padding=CARD_PAD,
        border_radius=CARD_RADIUS,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )
    stat_tasks_done = ft.Container(
        content=ft.Column(
            [ft.Text("Завершено задач", size=12, color=ft.colors.ON_SURFACE_VARIANT), tasks_done_val],
            spacing=4,
            tight=True,
        ),
        padding=CARD_PAD,
        border_radius=CARD_RADIUS,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )
    stat_processes = ft.Container(
        content=ft.Column(
            [ft.Text("Всего процессов", size=12, color=ft.colors.ON_SURFACE_VARIANT), procs_total_val],
            spacing=4,
            tight=True,
        ),
        padding=CARD_PAD,
        border_radius=CARD_RADIUS,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE),
    )

    return ft.View(
        route="/dashboard",
        controls=[
            navbar(page, "/dashboard"),
            ft.Container(height=8),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(col={"xs": 12, "md": 4}, controls=[stat_tasks_open]),
                    ft.Column(col={"xs": 12, "md": 4}, controls=[stat_tasks_done]),
                    ft.Column(col={"xs": 12, "md": 4}, controls=[stat_processes]),
                ],
                columns=12,
                spacing=12,
            ),
        ],
        padding=16,
        scroll=ft.ScrollMode.AUTO,
    )
