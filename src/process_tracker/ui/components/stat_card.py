from __future__ import annotations

from typing import Any

import flet as ft


def stat_card(title: str, value: Any, icon: str | None = None) -> ft.Container:
    """
    Небольшая карточка-метрика (для дашборда).
    """
    icn = getattr(ft.icons, icon, None) if isinstance(icon, str) else icon
    return ft.Container(
        padding=16,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.SURFACE_VARIANT),
        content=ft.Row(
            [
                ft.Container(
                    ft.Icon(icn or getattr(ft.icons, "INFO", None), size=24),
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.colors.with_opacity(0.08, ft.colors.SURFACE_VARIANT),
                ),
                ft.Column(
                    [
                        ft.Text(title, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Text(str(value), size=20, weight=ft.FontWeight.W_700),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=12,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
