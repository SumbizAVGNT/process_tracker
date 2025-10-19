from __future__ import annotations
import flet as ft

# Шим для icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

# ---------- helpers ----------
def _icon_value(icon: str | ft.Icon | None) -> str | None:
    if icon is None:
        return None
    if isinstance(icon, ft.Icon):
        return icon.name
    if isinstance(icon, str):
        if hasattr(ft.icons, icon):
            return getattr(ft.icons, icon)
        up = icon.upper()
        if hasattr(ft.icons, up):
            return getattr(ft.icons, up)
        return icon
    return None

def _is_active(current: str, route: str) -> bool:
    c = (current or "").rstrip("/")
    r = (route or "").rstrip("/")
    return c == r or (r and c.startswith(r + "/"))

def _chip(text: str, icon: str | ft.Icon | None, *, active: bool, on_click) -> ft.Control:
    style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=14),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )
    icon_name = _icon_value(icon)
    content = ft.Row(
        [
            ft.Icon(icon_name, size=16) if icon_name else ft.Container(width=0),
            ft.Text(text, size=13, weight="w600"),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    btn_cls = ft.FilledButton if active else ft.OutlinedButton
    return btn_cls(content=content, style=style, on_click=on_click)

# ---------- public API ----------
def navbar(page: ft.Page, active_route: str) -> ft.Container:
    # Без "Создать задачу" — кнопка останется в действиях страниц
    items = [
        ("/dashboard", "Дашборд", "DASHBOARD" if hasattr(ft.icons, "DASHBOARD") else "HOME"),
        ("/processes", "Процессы", "TIMELINE" if hasattr(ft.icons, "TIMELINE") else "LIST"),
        ("/settings", "Настройки", "SETTINGS"),
    ]

    row = ft.Row(
        [
            _chip(
                title,
                icon,
                active=_is_active(active_route, route),
                on_click=lambda _e, r=route: page.go(r),
            )
            for route, title, icon in items
        ],
        spacing=10,
        wrap=False,
        scroll=ft.ScrollMode.AUTO,  # горизонтальный скролл при узком экране
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.START,
    )

    return ft.Container(
        content=row,
        padding=ft.padding.symmetric(horizontal=8, vertical=8),
        border=ft.border.all(1, ft.colors.with_opacity(0.06, getattr(ft.colors, "ON_SURFACE", ft.colors.WHITE))),
        border_radius=14,
        bgcolor=ft.colors.with_opacity(0.04, getattr(ft.colors, "SURFACE", ft.colors.BLUE_GREY_900)),
    )
