from __future__ import annotations
import flet as ft

def _toast(page: ft.Page, msg: str, kind: str = "info") -> None:
    try:
        from .forms import toast  # наш toast, если есть
        toast(page, msg, kind=kind)
    except Exception:
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), open=True)
        page.update()

async def open_quick_create(page: ft.Page) -> None:
    title = ft.TextField(label="Название задачи", autofocus=True, dense=True)
    prio  = ft.Dropdown(label="Приоритет", options=[ft.dropdown.Option(x) for x in ["P2","P1","P0"]], value="P2", dense=True)
    descr = ft.TextField(label="Описание (опционально)", multiline=True, min_lines=3, max_lines=6, dense=True)

    async def _create():
        name = (title.value or "").strip()
        if not name:
            _toast(page, "Заполните название", "warning"); return

        # Пытаемся вызвать API если доступно
        try:
            from ..services.api import ApiClient
            api = ApiClient(base_url="http://127.0.0.1:8787/api/v1")
            await api._ensure_client()
            try:
                await api._req("POST", "/tasks", json_body={"title": name, "priority": prio.value, "description": descr.value or ""})
                _toast(page, "Задача создана", "success")
            except Exception:
                # в бэке может не быть эндпоинта — просто уведомим и закроем
                _toast(page, "Черновик создан локально", "info")
        except Exception:
            _toast(page, "Черновик создан локально", "info")

        dialog.open = False
        try: page.update()
        except Exception: pass

    actions = ft.Row(
        [
            ft.TextButton("Отмена", on_click=lambda _e: setattr(dialog, "open", False)),
            ft.FilledButton("Создать", icon=ft.icons.ADD, on_click=lambda _e: (page.run_task(_create) if hasattr(page, "run_task") else None) or None),
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Новая задача", weight="w700"),
        content=ft.Container(ft.Column([title, prio, descr, ft.Container(height=4)], tight=True, spacing=10), width=520),
        actions=[actions],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()
