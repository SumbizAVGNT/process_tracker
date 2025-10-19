from __future__ import annotations
import asyncio
import flet as ft
from sqlalchemy import select, func

from ...db.session import AsyncSessionLocal
from ...db.models import Task, Process

try:
    from ..components.shell import page_scaffold
except ModuleNotFoundError:
    from ..shell import page_scaffold  # type: ignore

from ..components.stat_card import metric_tile
from ..components.forms import toast


# ── data ─────────────────────────────────────────────────────────────────────
async def _load_counts() -> tuple[int, int, int]:
    open_cnt = 0
    done_cnt = 0
    proc_cnt = 0
    async with AsyncSessionLocal() as s:
        try:
            proc_cnt = (await s.scalar(select(func.count()).select_from(Process))) or 0
        except Exception:
            proc_cnt = 0
        try:
            total = (await s.scalar(select(func.count()).select_from(Task))) or 0
        except Exception:
            total = 0
        try:
            if hasattr(Task, "status"):
                done_cnt = (await s.scalar(
                    select(func.count()).select_from(Task).where(Task.status == "done")
                )) or 0
                open_cnt = max(total - done_cnt, 0)
            else:
                open_cnt = total
        except Exception:
            open_cnt = total
            done_cnt = 0
    return open_cnt, done_cnt, proc_cnt


# ── view ─────────────────────────────────────────────────────────────────────
def view(page: ft.Page) -> ft.View:
    # крупные значения
    v_open = ft.Text("0", size=28, weight="w800")
    v_done = ft.Text("0", size=28, weight="w800")
    v_proc = ft.Text("0", size=28, weight="w800")

    async def refresh():
        try:
            o, d, p = await _load_counts()
            v_open.value, v_done.value, v_proc.value = str(o), str(d), str(p)
            try: page.update()
            except Exception: pass
        except Exception as e:  # noqa: BLE001
            toast(page, f"Не удалось обновить: {e}", kind="error")

    # первая загрузка — безопасно планируем
    try:
        page.run_task(refresh)
    except Exception:
        try:
            asyncio.get_running_loop().create_task(refresh())
        except RuntimeError:
            asyncio.run(refresh())

    # hero-шапка с маленькими икон-шорткатами
    hero = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Дашборд", size=24, weight="w800"),
                    ft.Text("Ключевые показатели и процессы проекта", color=ft.colors.ON_SURFACE_VARIANT),
                ],
                spacing=6, tight=True,
            ),
            ft.Container(expand=True),
            ft.Row(
                [
                    ft.IconButton(icon=ft.icons.ADD_TASK, tooltip="Новая задача", on_click=lambda _e: page.go("/tasks/create")),
                    ft.IconButton(icon=ft.icons.TIMELINE, tooltip="Процессы", on_click=lambda _e: page.go("/processes")),
                    ft.IconButton(icon=ft.icons.SETTINGS, tooltip="Настройки", on_click=lambda _e: page.go("/settings")),
                ],
                spacing=6,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # KPI → ResponsiveRow (современно и адаптивно)
    grid = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=metric_tile(
                    "Открытые задачи", v_open, icon="WHATSHOT", tone="warning",
                    trend=[3, 4, 6, 5, 7, 6, 8, 7],
                    tooltip="Показать задачи / создать новую",
                    on_click=lambda _e: page.go("/tasks/create"),
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=metric_tile(
                    "Завершено задач", v_done, icon="CHECK_CIRCLE_OUTLINE", tone="success",
                    trend=[1, 2, 2, 3, 4, 5, 6, 7],
                    tooltip="История завершения",
                    on_click=lambda _e: page.go("/tasks/create"),
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=metric_tile(
                    "Всего процессов", v_proc, icon="WORKSPACES_OUTLINED", tone="info",
                    trend=[2, 2, 3, 3, 3, 4, 4, 5],
                    tooltip="Открыть список процессов",
                    on_click=lambda _e: page.go("/processes"),
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
        ],
        columns=12,
        run_spacing=16,
        spacing=16,
    )

    # плавающая FAB (круглая, без текстов)
    try:
        page.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            tooltip="Создать задачу",
            mini=True,
            bgcolor=ft.colors.BLUE_ACCENT_400,
            on_click=lambda _e: page.go("/tasks/create"),
        )
    except Exception:
        pass

    body = ft.Column(
        [hero, ft.Container(height=8), grid],
        spacing=0,
        tight=True,
    )

    return page_scaffold(page, title="Дашборд", route="/dashboard", body=body)
