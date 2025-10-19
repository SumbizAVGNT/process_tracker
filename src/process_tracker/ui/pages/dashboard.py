from __future__ import annotations

import flet as ft
from sqlalchemy import select, func

from ...db.session import AsyncSessionLocal
from ...db.models import Task, Process
from ..components.shell import page_scaffold
from ..components.stat_card import metric_tile


# ── данные ───────────────────────────────────────────────────────────────────

async def _load_counts():
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
    # KPI значения (живые Text, чтобы обновлять без пересоздания контролов)
    v_open = ft.Text("0", size=24, weight="w800")
    v_done = ft.Text("0", size=24, weight="w800")
    v_proc = ft.Text("0", size=24, weight="w800")

    async def refresh():
        o, d, p = await _load_counts()
        v_open.value, v_done.value, v_proc.value = str(o), str(d), str(p)
        try:
            page.update()
        except Exception:
            pass

    try:
        page.run_task(refresh)
    except Exception:
        pass

    # Заголовок + компактные экшены справа
    actions = ft.Row(
        [
            ft.IconButton(ft.icons.REFRESH, tooltip="Обновить", on_click=lambda _e: page.run_task(refresh)),
            ft.IconButton(ft.icons.ADD_TASK, tooltip="Создать задачу", on_click=lambda _e: page.go("/tasks/create")),
            ft.IconButton(ft.icons.TIMELINE, tooltip="К процессам", on_click=lambda _e: page.go("/processes")),
            ft.IconButton(ft.icons.SETTINGS, tooltip="Настройки", on_click=lambda _e: page.go("/settings")),
        ],
        spacing=6,
    )

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Дашборд", size=22, weight="w800"),
                    ft.Text("Ключевые показатели проекта", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                ],
                spacing=3,
                tight=True,
            ),
            ft.Container(expand=True),
            actions,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # KPI-плитки: простая и 100% совместимая верстка
    # делаем фикс. ширину, чтобы Row с wrap корректно переносил их
    tile_w = 360
    tiles_row = ft.Row(
        [
            ft.Container(
                metric_tile("Открытые задачи", v_open, icon="WHATSHOT", tone="warning", width=tile_w, height=96),
                width=tile_w,
            ),
            ft.Container(
                metric_tile("Завершено задач", v_done, icon="CHECK_CIRCLE_OUTLINE", tone="success", width=tile_w, height=96),
                width=tile_w,
            ),
            ft.Container(
                metric_tile("Всего процессов", v_proc, icon="WORKSPACES_OUTLINED", tone="info", width=tile_w, height=96),
                width=tile_w,
            ),
        ],
        spacing=12,
        run_spacing=12,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    # Быстрые фильтры (плейсхолдер)
    def chip(text: str, active: bool = False, on_click=None) -> ft.Control:
        base = ft.FilledButton if active else ft.OutlinedButton
        return base(
            text,
            height=34,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(8, 14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=on_click,
        )

    filters = ft.Row(
        [chip("Мои", True), chip("Команда"), chip("Все"), chip("Неделя")],
        spacing=8,
        wrap=True,
    )

    # Карточка "Последние действия" — плейсхолдер
    def section_card(title: str, body: ft.Control, icon=None) -> ft.Container:
        head = ft.Row(
            [
                ft.Icon(icon or ft.icons.HISTORY_TOGGLE_OFF, size=16),
                ft.Text(title, size=13, color=ft.colors.ON_SURFACE_VARIANT),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        col = ft.Column([head, ft.Container(height=8), body], spacing=0, tight=True)
        return ft.Container(
            content=col,
            padding=14,
            border_radius=14,
            bgcolor=ft.colors.with_opacity(0.06, getattr(ft.colors, "SURFACE", ft.colors.BLUE_GREY_900)),
            border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE)),
        )

    recent_placeholder = ft.Column(
        [
            ft.Row(
                [ft.Icon(ft.icons.INBOX, size=16, opacity=0.7),
                 ft.Text("Нет недавней активности", color=ft.colors.ON_SURFACE_VARIANT)],
                spacing=8,
            ),
            ft.Text("Задачи и процессы появятся здесь, как только начнёте работать.",
                    size=12, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        spacing=6,
        tight=True,
    )

    body = ft.Column(
        [
            header,
            ft.Container(height=10),
            tiles_row,
            ft.Container(height=14),
            filters,
            ft.Container(height=14),
            section_card("Последние действия", recent_placeholder, icon=ft.icons.HISTORY),
        ],
        spacing=0,
        tight=True,
    )

    return page_scaffold(page, title="Дашборд", route="/dashboard", body=body)
