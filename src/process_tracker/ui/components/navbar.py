from __future__ import annotations
import flet as ft

# Шим для icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

def _chip(text: str, icon: str | None, *, active: bool, on_click) -> ft.Control:
    base = (ft.ElevatedButton if active else ft.OutlinedButton)
    return base(text, icon=icon, on_click=on_click, height=34)

def navbar(page: ft.Page, active_route: str) -> ft.Container:
    items = [
        ("/dashboard", "Дашборд", getattr(ft.icons, "DASHBOARD", None) or getattr(ft.icons, "HOME", None)),
        ("/processes", "Процессы", getattr(ft.icons, "TIMELINE", None) or getattr(ft.icons, "LIST", None)),
        ("/tasks/create", "Создать задачу", getattr(ft.icons, "ADD_TASK", None) or getattr(ft.icons, "ADD", None)),
        ("/settings", "Настройки", getattr(ft.icons, "SETTINGS", None)),
    ]
    row = ft.Row(
        [_chip(title, icon, active=(active_route == route), on_click=lambda _e, r=route: page.go(r))
         for route, title, icon in items],
        spacing=10,
        wrap=False,
    )
    return ft.Container(row, padding=ft.padding.symmetric(8, 8))
