from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
import re
import asyncio
import flet as ft

# Совместимость с разными версиями Flet
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

# ── Мягкие зависимости
try:
    from ...services.forms_service import FormSchema, FieldSchema, FieldOption  # type: ignore
except Exception:  # pragma: no cover
    FormSchema = FieldSchema = FieldOption = object  # type: ignore

# toast / async_button — можно не иметь модуль forms
try:
    from .forms import async_button, toast  # type: ignore
except Exception:  # pragma: no cover
    def toast(page: ft.Page, message: str, *, kind: str = "info", duration_ms: int = 2500) -> None:
        page.snack_bar = ft.SnackBar(content=ft.Text(message), open=True, duration=duration_ms)
        page.update()

    def async_button(page: ft.Page | None, text: str, *, task_factory=None, icon=None, **kw) -> ft.FilledButton:
        async def _noop(): ...
        btn = ft.FilledButton(text, icon=icon)
        def _h(_e):
            loop = asyncio.get_running_loop()
            loop.create_task((task_factory or _noop)())
        btn.on_click = _h
        return btn


# ========================  УТИЛИТЫ / НОРМАЛИЗАЦИЯ  =========================

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _is_pydantic(v: Any) -> bool:
    return hasattr(v, "model_dump") and callable(getattr(v, "model_dump"))

def _to_dict(v: Any) -> Dict[str, Any]:
    if _is_pydantic(v):
        return v.model_dump()
    if isinstance(v, dict):
        return v
    return {}

def _norm_fields(fields: Any) -> List[Dict[str, Any]]:
    """
    Превратить разные формы описания полей в единый List[dict].
    Поддерживает:
      - list[dict]
      - list[FieldSchema]
      - list[tuple[str, dict|FieldSchema]] (например, если пришло .items())
      - dict[name] -> dict
    """
    res: List[Dict[str, Any]] = []
    if fields is None:
        return res

    if isinstance(fields, dict):
        fields = list(fields.values())

    if not isinstance(fields, (list, tuple)):
        return res

    for it in fields:
        # ("name", {...})
        if isinstance(it, tuple) and len(it) == 2:
            it = it[1]
        d = _to_dict(it)
        if not d:
            continue

        # options -> list[dict{value,label}]
        opts = d.get("options")
        if opts is not None:
            if isinstance(opts, dict):
                opts = list(opts.values())
            if isinstance(opts, (list, tuple)):
                norm: List[Dict[str, Any]] = []
                for o in opts:
                    if isinstance(o, tuple) and len(o) == 2:
                        o = o[1]
                    od = _to_dict(o)
                    if not od and isinstance(o, str):
                        od = {"value": o, "label": str(o)}
                    if od:
                        # единые ключи
                        od = {
                            "value": od.get("value", od.get("key", od.get("id"))),
                            "label": od.get("label", od.get("text", od.get("name", ""))),
                        }
                        norm.append(od)
                d["options"] = norm
            else:
                d["options"] = []
        res.append(d)
    return res

def _normalize_schema(schema: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    sch = _to_dict(schema)
    sch["fields"] = _norm_fields(sch.get("fields"))
    sch["title"] = sch.get("title") or "Форма"
    return sch

def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


# ===========================  ПОСТРОИТЕЛЬ ПОЛЕЙ  ===========================

def _text_field_base(label: str, *, hint: Optional[str] = None, value: Optional[str] = None) -> ft.TextField:
    return ft.TextField(label=label, hint_text=hint, value=value or "")

def build_schema_fields(schema: Union[Dict[str, Any], Any]) -> List[ft.Control]:
    """
    Создаёт контролы по схеме. Поддерживаемые типы:
      text/string, textarea, email, password, int/integer, float/number,
      select, switch/boolean/bool, checkbox, radio
    """
    sch = _normalize_schema(schema)
    controls: List[ft.Control] = []

    # Попробуем подтянуть кастомный PasswordField (мягко)
    PasswordFieldCls = None
    try:
        from .password_field import PasswordField as _PF  # type: ignore
        PasswordFieldCls = _PF
    except Exception:
        PasswordFieldCls = None

    for f in sch.get("fields", []):
        name: str = f.get("name") or ""
        title: str = f.get("title") or name or "Поле"
        ftype: str = (f.get("type") or "text").lower()
        required: bool = bool(f.get("required") or False)
        placeholder: Optional[str] = f.get("placeholder")
        default: Any = f.get("default", None)
        helper: Optional[str] = f.get("description") or f.get("help") or None

        label_text = f"{title}{' *' if required else ''}"

        # ---------- поля ----------
        if ftype in ("text", "string"):
            ctrl = _text_field_base(label_text, hint=placeholder, value=default)
        elif ftype == "textarea":
            ctrl = ft.TextField(
                label=label_text, hint_text=placeholder, value=default or "",
                multiline=True, min_lines=int(f.get("min_lines", 3)), max_lines=int(f.get("max_lines", 8))
            )
        elif ftype == "email":
            ctrl = ft.TextField(
                label=label_text, hint_text=placeholder or "name@company.com",
                value=default or "", keyboard_type=ft.KeyboardType.EMAIL
            )
        elif ftype == "password":
            if PasswordFieldCls:
                ctrl = PasswordFieldCls(label=label_text)
                if default:
                    ctrl.value = str(default)
            else:
                ctrl = ft.TextField(label=label_text, value=default or "", password=True, can_reveal_password=True)
        elif ftype in ("int", "integer"):
            ctrl = ft.TextField(
                label=label_text,
                value=str(default) if default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
            )
        elif ftype in ("float", "number", "decimal"):
            ctrl = ft.TextField(
                label=label_text,
                value=str(default) if default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
            )
        elif ftype in ("select", "choice"):
            opts = f.get("options") or []
            options = [
                ft.dropdown.Option(str(o.get("value")), o.get("label") or str(o.get("value")))
                for o in opts if isinstance(o, dict) and "value" in o
            ]
            ctrl = ft.Dropdown(
                label=label_text,
                options=options,
                value=str(default) if default is not None else (options[0].key if options else None),
            )
        elif ftype in ("switch", "boolean", "bool"):
            ctrl = ft.Switch(label=label_text, value=_bool(default))
        elif ftype == "checkbox":
            ctrl = ft.Checkbox(label=label_text, value=_bool(default))
        elif ftype == "radio":
            opts = f.get("options") or []
            rg_options = [
                ft.Radio(value=str(o.get("value")), label=o.get("label") or str(o.get("value")))
                for o in opts if isinstance(o, dict) and "value" in o
            ]
            ctrl = ft.RadioGroup(
                content=ft.Column(rg_options, tight=True, spacing=4),
                value=str(default) if default is not None else (rg_options[0].value if rg_options else None),
            )
            # подпись выведем отдельным Text рядом при отрисовке
            setattr(ctrl, "_df_label", label_text)
        else:
            ctrl = _text_field_base(label_text, hint=placeholder, value=default)

        # ---------- метаданные ----------
        setattr(ctrl, "_df_name", name)
        setattr(ctrl, "_df_type", ftype)
        setattr(ctrl, "_df_required", required)
        setattr(ctrl, "_df_meta", f)

        # helper / description
        if isinstance(ctrl, ft.TextField):
            ctrl.helper_text = helper

        controls.append(ctrl)

    return controls


# =============================  ДИНАМИЧЕСКАЯ ФОРМА  ==========================

class DynamicForm(ft.Container):
    """
    Карточка-форма:
      - без UserControl (совместимо со старыми Flet);
      - собирает и валидирует данные локально;
      - вызывает on_submit(data) если задан.
    """
    def __init__(
        self,
        schema: Union[Dict[str, Any], Any],
        on_submit: Optional[Callable[[Dict[str, Any]], Awaitable[Any]]] = None,
        *,
        submit_text: str = "Создать",
        width: Optional[float] = 520,
        dense: bool = True,
    ) -> None:
        super().__init__()
        self._schema = _normalize_schema(schema)
        self._on_submit = on_submit
        self._submit_text = submit_text
        self._width = width
        self._dense = dense

        self._fields: List[ft.Control] = []

        # визуальные параметры карточки
        self.width = width
        self.padding = ft.padding.all(16)
        self.border_radius = 16
        self.border = ft.border.all(1, ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE))
        self.bgcolor = ft.colors.with_opacity(0.04, ft.colors.SURFACE)

        self._build_content()

    # ---- API ----

    def set_values(self, data: Dict[str, Any]) -> None:
        """Программно проставить значения по имени поля."""
        for c in self._fields:
            name = getattr(c, "_df_name", None)
            if not name or name not in data:
                continue
            val = data[name]
            try:
                if isinstance(c, ft.Dropdown):
                    c.value = None if val is None else str(val)
                elif isinstance(c, ft.Switch) or isinstance(c, ft.Checkbox):
                    c.value = _bool(val)
                elif isinstance(c, ft.RadioGroup):
                    c.value = None if val is None else str(val)
                elif isinstance(c, ft.TextField):
                    c.value = "" if val is None else str(val)
            except Exception:
                pass
        try:
            self.update()
        except Exception:
            pass

    # ---- helpers ----

    def _collect_values(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for c in self._fields:
            name: str = getattr(c, "_df_name", None)
            if not name:
                continue
            if isinstance(c, ft.Dropdown):
                data[name] = c.value
            elif isinstance(c, ft.RadioGroup):
                data[name] = c.value
            elif isinstance(c, ft.Switch) or isinstance(c, ft.Checkbox):
                data[name] = bool(c.value)
            elif isinstance(c, ft.TextField):
                v = c.value or ""
                ftype = getattr(c, "_df_type", "text")
                if ftype in ("int", "integer"):
                    try:
                        data[name] = int(v) if str(v).strip() else None
                    except Exception:
                        data[name] = v
                elif ftype in ("float", "number", "decimal"):
                    try:
                        data[name] = float(v) if str(v).strip() else None
                    except Exception:
                        data[name] = v
                else:
                    data[name] = v
            else:
                data[name] = getattr(c, "value", None)
        return data

    def _validate_local(self, data: Dict[str, Any]) -> Dict[str, str]:
        errors: Dict[str, str] = {}
        for c in self._fields:
            meta: Dict[str, Any] = getattr(c, "_df_meta", {}) or {}
            name: str = meta.get("name")
            ftype: str = (meta.get("type") or "text").lower()
            required: bool = bool(meta.get("required"))

            val = data.get(name)

            # required
            if required:
                if (val is None) or (isinstance(val, str) and not val.strip()):
                    errors[name] = "Обязательное поле"
                    continue
                if isinstance(val, bool) and ftype in ("switch", "boolean", "bool", "checkbox"):
                    # для булевых required= True значит, что должен быть True
                    if val is False:
                        errors[name] = "Необходимо включить"
                        continue

            if val is None or (isinstance(val, str) and not val.strip()):
                continue

            # длина для строковых
            if isinstance(val, str) and ftype in ("text", "textarea", "email", "password", "select"):
                mn = meta.get("min_length")
                mx = meta.get("max_length")
                if mn is not None and len(val) < int(mn):
                    errors[name] = f"Минимальная длина: {mn}"
                    continue
                if mx is not None and len(val) > int(mx):
                    errors[name] = f"Максимальная длина: {mx}"
                    continue

            # формат email
            if ftype == "email" and isinstance(val, str):
                if not _EMAIL_RE.match(val.strip()):
                    errors[name] = "Неверный формат email"
                    continue

            # числа
            if ftype in ("int", "integer"):
                try:
                    iv = int(val)
                except Exception:
                    errors[name] = "Ожидается целое число"
                    continue
                mn = meta.get("min_value")
                mx = meta.get("max_value")
                if mn is not None and iv < int(mn):
                    errors[name] = f"Минимум: {mn}"
                    continue
                if mx is not None and iv > int(mx):
                    errors[name] = f"Максимум: {mx}"
                    continue

            if ftype in ("float", "number", "decimal"):
                try:
                    fv = float(val)
                except Exception:
                    errors[name] = "Ожидается число"
                    continue
                mn = meta.get("min_value")
                mx = meta.get("max_value")
                if mn is not None and fv < float(mn):
                    errors[name] = f"Минимум: {mn}"
                    continue
                if mx is not None and fv > float(mx):
                    errors[name] = f"Максимум: {mx}"
                    continue

            # select / radio допустимые значения
            if ftype in ("select", "choice", "radio"):
                opts = meta.get("options") or []
                allowed = {str(o.get("value")) for o in opts if isinstance(o, dict)}
                if str(val) not in allowed:
                    errors[name] = "Недопустимое значение"
                    continue

        return errors

    async def _submit(self) -> None:
        data = self._collect_values()
        errors = self._validate_local(data)
        if errors:
            first = next(iter(errors))
            toast(self.page, f"Ошибка: {errors[first]}", kind="error")
            # подсветка
            for c in self._fields:
                nm = getattr(c, "_df_name", None)
                try:
                    if nm in errors:
                        if isinstance(c, ft.TextField):
                            c.border = ft.border.all(1, ft.colors.RED)
                            c.helper_text = errors[nm]
                        elif isinstance(c, (ft.Switch, ft.Checkbox)):
                            c.tooltip = errors[nm]
                    else:
                        if isinstance(c, ft.TextField):
                            c.border = None
                            c.helper_text = None
                        elif isinstance(c, (ft.Switch, ft.Checkbox)):
                            c.tooltip = None
                    c.update()
                except Exception:
                    pass
            return

        if self._on_submit:
            await self._on_submit(data)

    def _apply_field_widths(self) -> None:
        """Унифицируем ширины полей, если они не заданы явно."""
        if not self._width:
            return
        target = max(float(self._width) - 48, 320)
        for c in self._fields:
            try:
                # Не трогаем RadioGroup со своей колонкой
                if isinstance(c, ft.RadioGroup):
                    continue
                if getattr(c, "width", None) in (None, 0):
                    c.width = target
            except Exception:
                pass

    def _wrap_with_labels(self, controls: List[ft.Control]) -> List[ft.Control]:
        """Для RadioGroup показываем подпись сверху (label)."""
        out: List[ft.Control] = []
        for c in controls:
            lbl = getattr(c, "_df_label", None)
            if lbl:
                out.append(ft.Column([ft.Text(lbl), c], spacing=6, tight=True))
            else:
                out.append(c)
        return out

    def _build_content(self) -> None:
        title = self._schema.get("title") or "Форма"
        self._fields = build_schema_fields(self._schema)
        self._apply_field_widths()

        submit_btn = async_button(
            getattr(self, "page", None),
            self._submit_text,
            task_factory=self._submit,
            icon=getattr(ft.icons, "CHECK", None),
        )

        fields_block = self._wrap_with_labels(self._fields)

        col = ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.icons.TASK_ALT_OUTLINED, size=22), ft.Text(title, size=20, weight="w700")],
                    spacing=10,
                ),
                ft.Divider(opacity=0.06),
                *fields_block,
                ft.Container(height=8),
                ft.Row([submit_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=10,
            tight=True,
        )
        self.content = col
