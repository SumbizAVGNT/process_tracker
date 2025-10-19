from __future__ import annotations
import flet as ft

def empty_state(title: str, text: str, *, icon: str = "INBOX", action: ft.Control | None = None) -> ft.Container:
    content = ft.Column(
        [
            ft.Icon(getattr(ft.icons, icon, None), size=48, color=ft.colors.ON_SURFACE_VARIANT),
            ft.Text(title, size=18, weight="w700"),
            ft.Text(text, color=ft.colors.ON_SURFACE_VARIANT),
            ft.Container(height=6),
            action or ft.Container(),
        ],
        spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(content, alignment=ft.alignment.center, padding=30, border_radius=16,
                        border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.WHITE)))
