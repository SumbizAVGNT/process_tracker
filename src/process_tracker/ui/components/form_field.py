from __future__ import annotations

from typing import Any, Callable, Optional
import flet as ft


# ── helpers ──────────────────────────────────────────────────────────────────
def _icon_value(icon: str | ft.Icon | None) -> str | None:
    """
    Поддерживает:
      - "MAIL_OUTLINED" / "NUMBERS" (имя атрибута в ft.icons)
      - "mail_outlined" / "numbers" (готовое имя)
      - ft.icons.MAIL_OUTLINED
      - ft.Icon(name="mail_outlined")
    """
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
# ─────────────────────────────────────────────────────────────────────────────


def TextField(
    label: str,
    *,
    value: str | None = "",
    hint_text: str | None = None,
    icon: str | ft.Icon | None = None,
    on_submit: Optional[Callable[[ft.ControlEvent], Any]] = None,
    on_change: Optional[Callable[[ft.ControlEvent], Any]] = None,
    password: bool = False,
    multiline: bool = False,
    max_length: int | None = None,
    dense: bool = True,
    expand: int | bool | None = None,
    width: float | int | None = None,
    helper_text: str | None = None,
    error_text: str | None = None,
    **extra,  # любой доп. параметр Flet (keyboard_type, prefix_text и т.п.)
) -> ft.TextField:
    """Универсальный текстовый инпут с единым стилем."""
    return ft.TextField(
        label=label,
        value=value or "",
        hint_text=hint_text,
        prefix_icon=_icon_value(icon),
        password=bool(password),
        can_reveal_password=False,  # раскрытие — в PasswordField
        multiline=bool(multiline),
        max_length=max_length,
        dense=dense,
        expand=expand,
        width=width,
        helper_text=helper_text,
        error_text=error_text,
        on_submit=on_submit,
        on_change=on_change,
        **extra,
    )


def EmailField(label: str = "Email", **kwargs) -> ft.TextField:
    kwargs.setdefault("keyboard_type", ft.KeyboardType.EMAIL)
    kwargs.setdefault("icon", "MAIL_OUTLINED")
    return TextField(label, hint_text="name@company.com", **kwargs)


def IntegerField(
    label: str,
    *,
    allow_negative: bool = False,
    allow_empty: bool = True,
    icon: str | ft.Icon | None = "NUMBERS",
    **kwargs,
) -> ft.TextField:
    """
    Целочисленное поле:
      - allow_empty=True → позволяет пустую строку;
      - allow_negative=True → разрешает ведущий «-».
    """
    tf = TextField(label, icon=icon, keyboard_type=ft.KeyboardType.NUMBER, **kwargs)

    # Фильтр на всё значение (а не по символам)
    if allow_negative:
        pattern = r"^-?[0-9]*$" if allow_empty else r"^-?[0-9]+$"
    else:
        pattern = r"^[0-9]*$" if allow_empty else r"^[0-9]+$"

    tf.input_filter = ft.InputFilter(allow=True, regex_string=pattern)
    return tf
