from __future__ import annotations
import flet as ft


# --- helpers -----------------------------------------------------------------
def _icon_value(icon: str | ft.Icon | None) -> str | None:
    """
    Возвращает корректное значение для параметра icon в кнопках Flet.
    Поддерживает:
      - "ADD" / "LOGIN" (имя атрибута из ft.icons)
      - "add" / "login" (готовое строковое имя иконки)
      - ft.icons.ADD (то же, что "add")
      - ft.Icon(name="add")  → "add"
    """
    if icon is None:
        return None
    if isinstance(icon, ft.Icon):
        return icon.name

    if isinstance(icon, str):
        # уже готовое имя иконки? (обычно в нижнем регистре)
        if hasattr(ft.icons, icon):
            # на случай, если передали "ADD" и такое свойство реально есть
            return getattr(ft.icons, icon)

        # попробуем в верхнем регистре как имя атрибута
        up = icon.upper()
        if hasattr(ft.icons, up):
            return getattr(ft.icons, up)

        # иначе считаем, что это уже валидное имя ("add", "login"...)
        return icon

    # неизвестный тип — не ломаемся, просто не ставим иконку
    return None
# -----------------------------------------------------------------------------


def PrimaryButton(
    text: str,
    *,
    icon: str | ft.Icon | None = None,
    on_click=None,
    disabled: bool = False,
    expand: int | bool | None = None,
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text,
        icon=_icon_value(icon),
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        ),
    )


def SecondaryButton(
    text: str,
    *,
    icon: str | ft.Icon | None = None,
    on_click=None,
    disabled: bool = False,
    expand: int | bool | None = None,
) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text=text,
        icon=_icon_value(icon),
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        ),
    )


class LoadingButton(ft.ElevatedButton):
    """
    Кнопка со спиннером: btn.set_loading(True/False)
    Сохраняет текст и иконку, чтобы потом восстановить.
    """

    def __init__(
        self,
        text: str,
        *,
        icon: str | ft.Icon | None = None,
        on_click=None,
        expand: int | bool | None = None,
    ):
        super().__init__(
            text=text,
            icon=_icon_value(icon),
            on_click=on_click,
            expand=expand,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
        )
        self._saved_text = text
        self._saved_icon = self.icon

    def set_loading(self, value: bool = True) -> None:
        if value:
            # Блокируем и показываем спиннер + тот же текст, чтобы ширина не прыгала
            self.disabled = True
            self.content = ft.Row(
                [
                    ft.ProgressRing(width=16, height=16),
                    ft.Text(self._saved_text),
                ],
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            # уберём «иконку» уровня ElevatedButton, чтобы не дублировалась
            self.icon = None
        else:
            self.disabled = False
            self.content = None
            self.text = self._saved_text
            self.icon = self._saved_icon
        try:
            self.update()
        except Exception:
            # на случай вызова до монтирования на страницу
            pass
