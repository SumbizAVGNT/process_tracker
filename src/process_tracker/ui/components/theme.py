from __future__ import annotations
import flet as ft

if not hasattr(ft, "icons") and hasattr(ft, "Icons"): ft.icons = ft.Icons  # type: ignore
if not hasattr(ft, "colors") and hasattr(ft, "Colors"): ft.colors = ft.Colors  # type: ignore
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"): ft.alignment = ft.Alignment  # type: ignore
if hasattr(ft, "colors") and not hasattr(ft.colors, "with_opacity"):
    def _with_opacity(opacity: float, color: str) -> str: return color
    ft.colors.with_opacity = staticmethod(_with_opacity)  # type: ignore

RADIUS = 14

def glass(content: ft.Control, *, padding: int = 14) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=ft.colors.with_opacity(0.06, getattr(ft.colors, "SURFACE", "#121212")),
        border_radius=RADIUS,
        border=ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE)),
    )

def card(title: str | ft.Control, body: ft.Control | None = None, *, icon: str | None = None) -> ft.Container:
    header = ft.Row(
        [
            ft.Icon(icon, size=16) if icon else ft.Container(width=0),
            title if isinstance(title, ft.Control) else ft.Text(title, size=13, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    children = [header]
    if body is not None: children += [ft.Container(height=8), body]
    return glass(ft.Column(children, spacing=6), padding=12)

def kpi(label: str, value: str | ft.Text, *, icon: str | None = None) -> ft.Container:
    if not isinstance(value, ft.Text):
        value = ft.Text(value, size=22, weight="w800")
    body = ft.Column(
        [
            ft.Row(
                [ft.Icon(icon, size=16) if icon else ft.Container(width=0),
                 ft.Text(label, size=12, color=ft.colors.ON_SURFACE_VARIANT)],
                spacing=8, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            value,
        ],
        spacing=6, tight=True,
    )
    return glass(body, padding=14)
