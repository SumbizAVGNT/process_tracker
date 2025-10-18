# src/process_tracker/ui/components/forms.py
from __future__ import annotations

from typing import Any, Awaitable, Callable

import flet as ft

from .dynamic_form import DynamicForm, build_schema_fields
from .form_field import TextField, EmailField, IntegerField
from .password_field import PasswordField
from .button import LoadingButton
from ...core.asyncio_tools import fire_and_forget


def async_button(
    text: str,
    *,
    icon: str | None = None,
    on_click_async: Callable[[ft.ControlEvent], Awaitable[Any]],
    disabled: bool = False,
    expand: int | None = None,
) -> LoadingButton:
    """
    Кнопка, которая выполняет async-обработчик:
      btn = async_button("Сохранить", on_click_async=handle_save)
    Параллельно показывает/скрывает лоадер и не блокирует UI.
    """
    btn = LoadingButton(text, icon=icon)
    btn.disabled = disabled
    if expand is not None:
        btn.expand = expand

    def _handler(e: ft.ControlEvent) -> None:
        async def _run():
            btn.set_loading(True)
            try:
                await on_click_async(e)
            finally:
                btn.set_loading(False)

        fire_and_forget(_run(), name="async_button")

    btn.on_click = _handler
    return btn


__all__ = [
    "DynamicForm",
    "build_schema_fields",
    "TextField",
    "EmailField",
    "IntegerField",
    "PasswordField",
    "async_button",
]
