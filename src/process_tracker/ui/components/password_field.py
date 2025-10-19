from __future__ import annotations
import flet as ft


# Шим для icons на старых версиях Flet
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]


def _icon_value(icon: str | ft.Icon | None) -> str | None:
    """Приводим иконку к строковому имени, понимаем 'VISIBILITY', 'visibility', ft.icons.VISIBILITY, ft.Icon(...)."""
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


class PasswordField(ft.TextField):
    """
    Текстовое поле с переключателем видимости.
    Совместимо со старыми/новыми версиями Flet.
    """

    def __init__(
        self,
        label: str = "Пароль",
        *,
        value: str | None = "",
        hint_text: str | None = None,
        dense: bool = True,
        on_submit=None,
        reveal_toggle: bool = True,          # можно отключить кнопку-глазик
        expand: int | bool | None = None,
        width: float | int | None = None,
        helper_text: str | None = None,
        error_text: str | None = None,
    ):
        super().__init__(
            label=label,
            value=value or "",
            hint_text=hint_text,
            password=True,
            can_reveal_password=False,       # раскрытие — вручную через кнопку
            dense=dense,
            on_submit=on_submit,
            expand=expand,
            width=width,
            helper_text=helper_text,
            error_text=error_text,
        )
        self._visible = False

        if reveal_toggle:
            self.suffix = ft.IconButton(
                icon=_icon_value("VISIBILITY_OFF"),
                tooltip="Показать/скрыть",
                icon_size=18,
                on_click=self._toggle,
            )

    # Публичные helpers
    def set_visible(self, visible: bool) -> None:
        """Программно переключить видимость."""
        self._visible = bool(visible)
        self.password = not self._visible
        if isinstance(self.suffix, ft.IconButton):
            self.suffix.icon = _icon_value("VISIBILITY" if self._visible else "VISIBILITY_OFF")
        try:
            self.update()
        except Exception:
            pass

    def toggle(self) -> None:
        """Поменять видимость."""
        self.set_visible(not self._visible)

    # Внутренний обработчик
    def _toggle(self, _e=None):
        self.toggle()
