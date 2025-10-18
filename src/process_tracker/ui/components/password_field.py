from __future__ import annotations

import flet as ft


class PasswordField(ft.TextField):
    """
    Текстовое поле с переключателем видимости.
    Совместимо со старыми/новыми версиями Flet.
    """

    def __init__(self, label: str = "Пароль", *, dense: bool = True, on_submit=None):
        super().__init__(
            label=label,
            password=True,
            can_reveal_password=False,
            dense=dense,
            on_submit=on_submit,
        )
        self._visible = False
        self.suffix = ft.IconButton(
            icon=getattr(ft.icons, "VISIBILITY_OFF", None),
            tooltip="Показать/скрыть",
            on_click=self._toggle,
        )

    def _toggle(self, _e=None):
        self._visible = not self._visible
        self.password = not self._visible
        self.suffix.icon = getattr(ft.icons, "VISIBILITY", None) if self._visible else getattr(ft.icons, "VISIBILITY_OFF", None)
        self.update()
