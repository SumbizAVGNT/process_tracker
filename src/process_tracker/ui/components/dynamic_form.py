from __future__ import annotations

from typing import Any, Iterable, List, Dict

import flet as ft

# Совместимость: icons/Icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
    ft.icons = ft.Icons  # type: ignore[attr-defined]

from .form_field import TextField, EmailField, IntegerField
from .password_field import PasswordField


def _dropdown_options(options: Iterable[Any]) -> list[ft.dropdown.Option]:
    res: list[ft.dropdown.Option] = []
    for item in options or []:
        if isinstance(item, dict):
            res.append(ft.dropdown.Option(item.get("value"), item.get("label") or item.get("value")))
        else:
            res.append(ft.dropdown.Option(item, str(item)))
    return res


def build_schema_fields(schema: Iterable[Dict[str, Any]]) -> List[ft.Control]:
    """
    Преобразует простую схему в список Flet-контролов.
    Схема: список словарей с ключами:
      - name (str, обязательно)
      - type: text|email|password|integer|textarea|checkbox|select
      - label, hint, required, options (для select), multiline_rows, icon
      - value (значение по умолчанию)
    """
    controls: list[ft.Control] = []

    for f in schema or []:
        ftype = (f.get("type") or "text").lower()
        name = f.get("name") or ""
        label = f.get("label") or name.title()
        hint = f.get("hint")
        icon = f.get("icon")
        value = f.get("value")

        if ftype in ("text", "string"):
            ctrl = TextField(label, value=value or "", hint_text=hint, icon=icon)
        elif ftype == "email":
            ctrl = EmailField(label, value=value or "", hint_text=hint)
        elif ftype in ("password", "secret"):
            ctrl = PasswordField(label)
            if value:
                ctrl.value = str(value)
        elif ftype in ("int", "integer", "number"):
            ctrl = IntegerField(label, value=str(value or ""))
        elif ftype in ("textarea", "multiline"):
            rows = int(f.get("multiline_rows") or 4)
            ctrl = ft.TextField(
                label=label,
                value=value or "",
                hint_text=hint,
                multiline=True,
                min_lines=max(3, rows),
                max_lines=max(3, rows),
                dense=True,
            )
        elif ftype in ("checkbox", "bool", "boolean"):
            ctrl = ft.Checkbox(label=label, value=bool(value))
        elif ftype in ("select", "dropdown", "choice"):
            ctrl = ft.Dropdown(
                label=label,
                value=value,
                options=_dropdown_options(f.get("options") or []),
                dense=True,
            )
        else:
            # неизвестный тип — рендерим как обычный текст
            ctrl = TextField(label, value=value or "", hint_text=hint, icon=icon)

        # сохраняем имя поля для последующего извлечения данных
        ctrl.data = {"name": name}
        controls.append(ctrl)

    return controls


class DynamicForm(ft.Column):
    """
    Простейший DynamicForm:
      form = DynamicForm(schema, on_submit=lambda data: ...)
      data -> dict[name] = value
    """

    def __init__(self, schema: Iterable[Dict[str, Any]], *, on_submit=None, submit_text: str = "Сохранить"):
        super().__init__(spacing=12, tight=True)

        self._fields: list[ft.Control] = build_schema_fields(schema)

        submit_btn = ft.FilledButton(
            submit_text,
            icon=getattr(ft.icons, "CHECK", None),
            on_click=lambda _e: on_submit and on_submit(self.value_dict()),
        )

        self.controls = [*self._fields, ft.Row([submit_btn], alignment=ft.MainAxisAlignment.END)]

    # Извлечение значений
    def value_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for c in self._fields:
            name = (getattr(c, "data", {}) or {}).get("name")
            if not name:
                continue
            if isinstance(c, ft.Checkbox):
                data[name] = bool(c.value)
            else:
                data[name] = getattr(c, "value", None)
        return data
