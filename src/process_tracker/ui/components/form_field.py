from __future__ import annotations

from typing import Any, Callable, Optional

import flet as ft


def TextField(
    label: str,
    *,
    value: str | None = "",
    hint_text: str | None = None,
    icon: str | None = None,
    on_submit: Optional[Callable[[ft.ControlEvent], Any]] = None,
    password: bool = False,
    multiline: bool = False,
    max_length: int | None = None,
    dense: bool = True,
) -> ft.TextField:
    """Универсальный текстовый инпут с единым стилем."""
    return ft.TextField(
        label=label,
        value=value or "",
        hint_text=hint_text,
        prefix_icon=getattr(ft.icons, icon, None) if isinstance(icon, str) else icon,
        password=password,
        can_reveal_password=False,  # ручное раскрытие делаем в PasswordField
        multiline=multiline,
        max_length=max_length,
        dense=dense,
        on_submit=on_submit,
    )


def EmailField(label: str = "Email", **kwargs) -> ft.TextField:
    return TextField(label, hint_text="name@company.com", icon="MAIL_OUTLINED", **kwargs)


def IntegerField(label: str, **kwargs) -> ft.TextField:
    tf = TextField(label, icon="NUMBERS", **kwargs)
    tf.input_filter = ft.InputFilter(allow=True, regex_string=r"[0-9]")
    return tf
