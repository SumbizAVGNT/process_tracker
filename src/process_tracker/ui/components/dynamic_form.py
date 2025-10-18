from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable

import flet as ft

from ...core.forms.schemas import FormSchema, FieldSchema, FieldType, FieldOption
from ...core.forms.validators import validate_data


class DynamicForm(ft.Column):
    """
    Универсальная форма на основе FormSchema.
    - Рендерит поля из схемы (TEXT, TEXTAREA, SELECT, MULTISELECT, DATE, USER)
    - Собирает значения -> validate_data() -> подсвечивает ошибки
    - Вызывает on_submit(values) при успешной валидации

    Использование:
        form = DynamicForm(schema, initial={"priority": "P2"}, on_submit=handle_submit)
        page.add(form)
    """

    def __init__(
        self,
        schema: FormSchema,
        *,
        initial: Optional[Dict[str, Any]] = None,
        on_submit: Optional[Callable[[Dict[str, Any]], Any]] = None,
        submit_text: str = "Сохранить",
        dense: bool = True,
    ):
        super().__init__(spacing=12, tight=True)
        self.schema = schema
        self.initial = initial or {}
        self.on_submit = on_submit
        self.submit_text = submit_text
        self.dense = dense

        self.controls_map: Dict[str, ft.Control] = {}
        self._errors_labels: Dict[str, ft.Text] = {}

        self._build()

    # ---------- Public API ----------

    def values(self) -> Dict[str, Any]:
        """Собрать значения из контролов."""
        data: Dict[str, Any] = {}
        for f in self.schema.fields:
            fid = f.id
            ctrl = self.controls_map.get(fid)
            if ctrl is None:
                continue
            data[fid] = self._extract_value(f, ctrl)
        return data

    async def validate_and_submit(self, _e=None) -> None:
        """Валидируем и если ок — вызываем on_submit(values)."""
        data = self.values()
        ok, errors = validate_data(self.schema, data)
        self._show_errors(errors)
        self.update()
        if ok and self.on_submit:
            res = self.on_submit(data)
            if hasattr(res, "__await__"):  # поддержка async колбэков
                await res  # type: ignore[misc]

    # ---------- Internal ----------

    def _build(self) -> None:
        header = ft.Text(self.schema.name, size=18, weight=ft.FontWeight.W_600)
        self.controls.append(header)

        # Поля
        for field in self.schema.fields:
            ctrl = self._build_field(field)
            self.controls_map[field.id] = ctrl
            self.controls.append(ctrl)
            # Подпись ошибок под полем (многострочно)
            err_lbl = ft.Text("", size=12, color=getattr(ft.colors, "ERROR", "#ff4d4f"))
            err_lbl.visible = False
            self._errors_labels[field.id] = err_lbl
            self.controls.append(err_lbl)

        # Кнопки
        btn_row = ft.Row(
            [
                ft.ElevatedButton(
                    self.submit_text,
                    icon=getattr(ft.icons, "TASK_ALT_OUTLINED", None),
                    on_click=self.validate_and_submit,
                )
            ],
            alignment=ft.MainAxisAlignment.END,
        )
        self.controls.append(ft.Container(height=4))
        self.controls.append(btn_row)

    def _build_field(self, f: FieldSchema) -> ft.Control:
        label = f.label or f.id
        value = self.initial.get(f.id)

        common_tf_kwargs = dict(
            label=label + (" *" if f.required else ""),
            dense=self.dense,
            value=str(value) if value is not None else "",
        )

        if f.type == FieldType.TEXT:
            return ft.TextField(
                **common_tf_kwargs,
                multiline=False,
                max_length=f.max_length,
                helper_text=(f.ui or {}).get("placeholder", None),
            )

        if f.type == FieldType.TEXTAREA:
            ui = f.ui or {}
            return ft.TextField(
                **common_tf_kwargs,
                multiline=True,
                min_lines=int(ui.get("min_lines") or 3),
                max_lines=int(ui.get("max_lines") or 8),
                max_length=f.max_length,
            )

        if f.type == FieldType.DATE:
            # безопасная реализация через TextField (YYYY-MM-DD)
            # DatePicker можно добавить позже через overlays
            return ft.TextField(
                **common_tf_kwargs,
                hint_text="YYYY-MM-DD",
            )

        if f.type == FieldType.USER:
            # пока просто email/логин; позже — автокомплит из API
            return ft.TextField(
                **common_tf_kwargs,
                hint_text=(f.ui or {}).get("hint", "email исполнителя"),
            )

        if f.type == FieldType.SELECT:
            options = [
                ft.dropdown.Option(str(opt.value), str(opt.label or opt.value))
                for opt in (f.options or [])
            ]
            return ft.Dropdown(
                label=label + (" *" if f.required else ""),
                dense=self.dense,
                options=options,
                value=str(value) if value is not None else (options[0].key if options else None),
            )

        if f.type == FieldType.MULTISELECT:
            # Рендерим как набор чекбоксов
            selected = set(value or [])
            checks: List[ft.Control] = []
            for opt in (f.options or []):
                cb = ft.Checkbox(
                    label=str(opt.label or opt.value),
                    value=str(opt.value) in selected,
                )
                cb.data = str(opt.value)
                checks.append(cb)
            wrap = ft.Column(checks, spacing=4)
            wrap.data = {"_multiselect": True}  # пометка типа
            wrap.tooltip = label + (" *" if f.required else "")
            return ft.Container(content=wrap, padding=ft.padding.symmetric(0, 4))

        # fallback — простой текст
        return ft.TextField(**common_tf_kwargs)

    def _extract_value(self, f: FieldSchema, ctrl: ft.Control) -> Any:
        if f.type in (FieldType.TEXT, FieldType.TEXTAREA, FieldType.DATE, FieldType.USER):
            return getattr(ctrl, "value", None)

        if f.type == FieldType.SELECT:
            return getattr(ctrl, "value", None)

        if f.type == FieldType.MULTISELECT:
            # собираем по чекбоксам
            content = getattr(ctrl, "content", None)
            if isinstance(content, ft.Column):
                vals: List[str] = []
                for c in content.controls:
                    if isinstance(c, ft.Checkbox) and c.value:
                        vals.append(str(c.data))
                return vals
            return []

        # дефолт
        return getattr(ctrl, "value", None)

    def _show_errors(self, errors: Dict[str, List[str]]) -> None:
        # Очистить все
        for fid, ctrl in self.controls_map.items():
            if hasattr(ctrl, "error_text"):
                setattr(ctrl, "error_text", None)
            lbl = self._errors_labels.get(fid)
            if lbl:
                lbl.visible = False
                lbl.value = ""

        # Поставить новые
        for fid, messages in errors.items():
            ctrl = self.controls_map.get(fid)
            msg = "; ".join(messages)
            if hasattr(ctrl, "error_text"):
                setattr(ctrl, "error_text", msg)
            lbl = self._errors_labels.get(fid)
            if lbl:
                lbl.visible = True
                lbl.value = msg
