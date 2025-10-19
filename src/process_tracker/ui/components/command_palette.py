from __future__ import annotations
from typing import Callable, List, Dict, Any, Optional
import flet as ft

# Мягкая иконка
def _icon(name: str) -> Any:
    return getattr(ft.icons, name, None)

Command = Dict[str, Any]  # {"label": str, "icon": str|None, "action": Callable[[], Awaitable|None]}

async def show_command_palette(page: ft.Page, commands: List[Command]) -> None:
    """
    Простая палитра команд на AlertDialog + фильтрация по вводу.
    action() может быть sync или async.
    """
    query = ft.TextField(
        hint_text="Искать действие… (например, «процессы»)",
        autofocus=True,
        dense=True,
        on_submit=lambda _e: _pick(0),
    )
    listview = ft.ListView(expand=True, spacing=2, padding=0, auto_scroll=False)
    dlg = ft.AlertDialog(modal=True, content=ft.Container(ft.Column([query, ft.Divider(opacity=0.06), listview], tight=True), width=520))
    page.dialog = dlg

    # — внутреннее состояние
    filtered: List[Command] = []

    def _refresh_list() -> None:
        q = (query.value or "").strip().lower()
        nonlocal filtered
        if q:
            filtered = [c for c in commands if q in c.get("label", "").lower()]
        else:
            filtered = commands[:]
        listview.controls = [
            ft.ListTile(
                leading=ft.Icon(_icon(c.get("icon"))) if c.get("icon") else None,
                title=ft.Text(c.get("label", "")),
                on_click=lambda _e, idx=i: _pick(idx),
                dense=True,
            ) for i, c in enumerate(filtered)
        ]
        try:
            listview.update()
        except Exception:
            pass

    def _pick(idx: int) -> None:
        if not (0 <= idx < len(filtered)):
            return
        dlg.open = False
        try: page.update()
        except Exception: pass

        action = filtered[idx].get("action")
        if action:
            res = action()
            # поддержим корутины и синхронные функции
            try:
                import asyncio
                if asyncio.iscoroutine(res):
                    if hasattr(page, "run_task"):
                        page.run_task(lambda: res)  # type: ignore[arg-type]
                    else:
                        asyncio.get_running_loop().create_task(res)  # type: ignore[arg-type]
            except Exception:
                pass

    query.on_change = lambda _e: _refresh_list()
    dlg.open = True
    page.update()
    _refresh_list()
