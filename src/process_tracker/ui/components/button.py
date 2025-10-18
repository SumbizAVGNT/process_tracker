from __future__ import annotations

import flet as ft


def PrimaryButton(
    text: str,
    *,
    icon: str | None = None,
    on_click=None,
    disabled: bool = False,
    expand: int | None = None,
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text,
        icon=getattr(ft.icons, icon, None) if isinstance(icon, str) else icon,
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(12, 16),
        ),
    )


def SecondaryButton(
    text: str,
    *,
    icon: str | None = None,
    on_click=None,
    disabled: bool = False,
    expand: int | None = None,
) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text,
        icon=getattr(ft.icons, icon, None) if isinstance(icon, str) else icon,
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(10, 14),
        ),
    )


class LoadingButton(ft.ElevatedButton):
    """
    Кнопка со спиннером: btn.set_loading(True/False)
    """

    def __init__(self, text: str, *, icon: str | None = None, on_click=None):
        super().__init__(
            text,
            icon=getattr(ft.icons, icon, None) if isinstance(icon, str) else icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(12, 16),
            ),
        )
        self._saved_text = text
        self._saved_icon = self.icon

    def set_loading(self, value: bool = True) -> None:
        if value:
            self.disabled = True
            self.text = "Подождите…"
            self.icon = None
            self.content = ft.Row(
                [ft.ProgressRing(width=16, height=16), ft.Text(self.text)],
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            self.disabled = False
            self.text = self._saved_text
            self.icon = self._saved_icon
            self.content = None
        self.update()
