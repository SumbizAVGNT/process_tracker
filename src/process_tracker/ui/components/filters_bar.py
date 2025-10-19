from __future__ import annotations
import flet as ft

def filters_bar(*controls: ft.Control) -> ft.Container:
    row = ft.Row(list(controls), spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(row, padding=10, border_radius=12,
                        border=ft.border.all(1, ft.colors.with_opacity(0.06, ft.colors.WHITE)),
                        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE))
