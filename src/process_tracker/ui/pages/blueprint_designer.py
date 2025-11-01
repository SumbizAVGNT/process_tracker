from __future__ import annotations
from typing import Any, Dict, List
from urllib.parse import urlparse, parse_qs

import flet as ft

from ..components.shell import page_scaffold
from ..components.theme import card
from ..components.forms import async_button, toast
from ..components.dynamic_form import DynamicForm
from ..state import state

# ------------------------------- storage in state.ctx -------------------------------

def _ctx_get(key: str, default):
    return state.ctx.get(key, default)

def _ctx_set(key: str, value) -> None:
    state.set_ctx(key, value)

def _load_types() -> List[Dict[str, Any]]:
    return list(_ctx_get("bp_types", []))

def _save_types(items: List[Dict[str, Any]]) -> None:
    _ctx_set("bp_types", items)

def _load_fields() -> Dict[str, List[Dict[str, Any]]]:
    return dict(_ctx_get("bp_fields", {}))

def _save_fields(data: Dict[str, List[Dict[str, Any]]]) -> None:
    _ctx_set("bp_fields", data)

def _load_routes() -> Dict[str, Dict[str, Any]]:
    return dict(_ctx_get("bp_routes", {}))  # {type_key: {"statuses": [], "transitions": []}}

def _save_routes(data: Dict[str, Dict[str, Any]]) -> None:
    _ctx_set("bp_routes", data)

# --------------------------------- helpers ----------------------------------

def _alpha(c: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, c)
    except Exception:
        return c

def _section_title(text: str) -> ft.Row:
    return ft.Row(
        [ft.Icon(ft.icons.TUNE, size=18), ft.Text(text, size=16, weight="w700")],
        spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

def _hbar(*controls: ft.Control) -> ft.Container:
    return ft.Container(
        ft.Row(list(controls), spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10, border_radius=12,
        border=ft.border.all(1, _alpha(ft.colors.WHITE, 0.06)),
        bgcolor=_alpha(ft.colors.SURFACE, 0.04),
    )

# --------------------------------- tabs -------------------------------------

def _tab_types(page: ft.Page) -> ft.Control:
    types = _load_types()

    # список типов
    table_rows: List[ft.DataRow] = []
    for t in types:
        table_rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(t.get("key", ""))),
                    ft.DataCell(ft.Text(t.get("name", ""))),
                    ft.DataCell(ft.Text(t.get("description", ""))),
                ]
            )
        )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Ключ")),
            ft.DataColumn(ft.Text("Название")),
            ft.DataColumn(ft.Text("Описание")),
        ],
        rows=table_rows,
        column_spacing=18,
        data_row_min_height=38,
        data_row_max_height=44,
        heading_row_height=38,
        divider_thickness=0,
    )

    # форма создания
    schema = {
        "title": "Новый тип процесса",
        "fields": [
            {"name": "key",         "title": "Ключ",       "type": "text",     "required": True, "min_length": 2, "max_length": 24},
            {"name": "name",        "title": "Название",   "type": "text",     "required": True, "min_length": 2},
            {"name": "description", "title": "Описание",   "type": "textarea", "required": False, "min_lines": 2, "max_lines": 5},
        ],
    }

    async def _create_type(data: Dict[str, Any]) -> None:
        key = (data.get("key") or "").strip()
        if any(t.get("key") == key for t in types):
            toast(page, "Тип с таким ключом уже есть", kind="warning"); return
        types.append({"key": key, "name": data.get("name"), "description": data.get("description", "")})
        _save_types(types)
        toast(page, "Тип добавлен", kind="success")
        page.go("/blueprint/designer?tab=types")

    form = DynamicForm(schema, on_submit=_create_type, submit_text="Добавить", width=520)

    left = card("Типы процессов", ft.Container(table, padding=0))
    right = card("Создание", ft.Container(form, padding=0), icon=ft.icons.ADD)

    return ft.Row([ft.Container(left, expand=2), ft.Container(right, expand=1)], spacing=12)

def _tab_forms(page: ft.Page) -> ft.Control:
    types = _load_types()
    fields_by_type = _load_fields()

    type_opts = [ft.dropdown.Option(t["key"], t["name"]) for t in types]
    type_dd = ft.Dropdown(label="Тип процесса", options=type_opts, value=(type_opts[0].key if type_opts else None), dense=True, width=320)

    # список полей текущего типа
    fields_list = ft.ListView(expand=True, spacing=4, padding=0)

    def _render_fields() -> None:
        k = type_dd.value
        arr = fields_by_type.get(k, [])
        fields_list.controls = [
            ft.ListTile(
                leading=ft.Icon(ft.icons.INPUT),
                title=ft.Text(f.get("title") or f.get("name")),
                subtitle=ft.Text(f'{f.get("type")} • {"обяз." if f.get("required") else "не обяз."}'),
                dense=True,
            )
            for f in arr
        ]
        try: fields_list.update()
        except Exception: pass

    type_dd.on_change = lambda _e: _render_fields()

    # форма поля
    field_schema = {
        "title": "Новое поле",
        "fields": [
            {"name": "name",     "title": "Имя",         "type": "text",   "required": True, "min_length": 2},
            {"name": "title",    "title": "Заголовок",   "type": "text",   "required": True},
            {"name": "type",     "title": "Тип",         "type": "select", "options": [
                {"value": "text", "label": "Текст"},
                {"value": "textarea", "label": "Многострочный текст"},
                {"value": "email", "label": "Email"},
                {"value": "password", "label": "Пароль"},
                {"value": "int", "label": "Целое"},
                {"value": "float", "label": "Число"},
                {"value": "select", "label": "Справочник"},
                {"value": "switch", "label": "Переключатель"},
                {"value": "checkbox", "label": "Чекбокс"},
                {"value": "radio", "label": "Радиокнопки"},
            ], "required": True, "default": "text"},
            {"name": "required", "title": "Обязательное", "type": "switch", "default": False},
            {"name": "options",  "title": "Опции (через запятую)", "type": "text", "description": "Для select/radio: value:label, value2:label2"},
        ],
    }

    async def _create_field(data: Dict[str, Any]) -> None:
        cur = type_dd.value
        if not cur:
            toast(page, "Выберите тип процесса", kind="warning"); return
        arr = fields_by_type.get(cur, [])
        # парсим options: "val:Label, val2" → [{"value":"val","label":"Label"}, {"value":"val2","label":"val2"}]
        opts_raw = (data.get("options") or "").strip()
        options: List[Dict[str, str]] = []
        if opts_raw:
            parts = [p.strip() for p in opts_raw.split(",") if p.strip()]
            for p in parts:
                if ":" in p:
                    v, l = p.split(":", 1)
                    options.append({"value": v.strip(), "label": l.strip()})
                else:
                    options.append({"value": p, "label": p})
        item = {
            "name": data["name"], "title": data["title"], "type": data["type"],
            "required": bool(data.get("required")), "options": options,
        }
        arr.append(item)
        fields_by_type[cur] = arr
        _save_fields(fields_by_type)
        toast(page, "Поле добавлено", kind="success")
        _render_fields()

    form = DynamicForm(field_schema, on_submit=_create_field, submit_text="Добавить поле", width=520)

    left = card("Поля выбранного типа", ft.Container(fields_list, padding=0))
    right = card("Добавить поле", ft.Container(form, padding=0), icon=ft.icons.ADD)

    # первичный рендер
    _render_fields()

    return ft.Row([ft.Container(left, expand=2), ft.Container(right, expand=1)], spacing=12)

def _tab_routes(page: ft.Page) -> ft.Control:
    types = _load_types()
    routes = _load_routes()
    type_opts = [ft.dropdown.Option(t["key"], t["name"]) for t in types]
    type_dd = ft.Dropdown(label="Тип процесса", options=type_opts, value=(type_opts[0].key if type_opts else None), dense=True, width=320)

    chips_row = ft.Row(spacing=6, wrap=True)
    trans_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("От")),
        ft.DataColumn(ft.Text("К")),
        ft.DataColumn(ft.Text("Условие/действие")),
    ], rows=[], column_spacing=18, data_row_min_height=38, data_row_max_height=44, heading_row_height=38, divider_thickness=0)

    status_tf = ft.TextField(label="Новый статус (ключ)", dense=True, width=220)
    from_dd = ft.Dropdown(label="От", dense=True, width=160)
    to_dd   = ft.Dropdown(label="К",  dense=True, width=160)
    cond_tf = ft.TextField(label="Условие/действие (опц.)", dense=True, width=260)

    def _ensure(model_key: str) -> Dict[str, Any]:
        if model_key not in routes:
            routes[model_key] = {"statuses": [], "transitions": []}
        return routes[model_key]

    def _refresh_ui() -> None:
        k = type_dd.value
        if not k:
            chips_row.controls = []
            trans_table.rows = []
            return
        m = _ensure(k)
        # статусы → чипсы
        chips_row.controls = [
            ft.Chip(label=s, leading=ft.Icon(ft.icons.LABEL_OUTLINED, size=14), bgcolor=_alpha(ft.colors.SURFACE, 0.06))
            for s in m["statuses"]
        ]
        # выпадающие списки
        opts = [ft.dropdown.Option(s) for s in m["statuses"]]
        from_dd.options = opts
        to_dd.options = opts
        # переходы
        trans_table.rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(t["from"])), ft.DataCell(ft.Text(t["to"])), ft.DataCell(ft.Text(t.get("cond","")))])
            for t in m["transitions"]
        ]
        try:
            chips_row.update(); from_dd.update(); to_dd.update(); trans_table.update()
        except Exception:
            pass

    async def _add_status() -> None:
        k = type_dd.value
        if not k: toast(page, "Выберите тип", kind="warning"); return
        name = (status_tf.value or "").strip()
        if not name: return
        m = _ensure(k)
        if name in m["statuses"]:
            toast(page, "Такой статус уже есть", kind="warning"); return
        m["statuses"].append(name)
        _save_routes(routes)
        status_tf.value = ""
        try: status_tf.update()
        except Exception: pass
        _refresh_ui()
        toast(page, "Статус добавлен", kind="success")

    async def _add_transition() -> None:
        k = type_dd.value
        if not k: toast(page, "Выберите тип", kind="warning"); return
        if not from_dd.value or not to_dd.value: return
        m = _ensure(k)
        m["transitions"].append({"from": from_dd.value, "to": to_dd.value, "cond": (cond_tf.value or "").strip()})
        _save_routes(routes)
        cond_tf.value = ""
        try: cond_tf.update()
        except Exception: pass
        _refresh_ui()
        toast(page, "Переход добавлен", kind="success")

    type_dd.on_change = lambda _e: _refresh_ui()
    _refresh_ui()

    actions = ft.Row(
        [
            ft.TextButton("Добавить статус", icon=ft.icons.ADD, on_click=lambda _e: page.run_task(_add_status) if hasattr(page, "run_task") else None),
            ft.TextButton("Добавить переход", icon=ft.icons.CALL_MADE, on_click=lambda _e: page.run_task(_add_transition) if hasattr(page, "run_task") else None),
        ],
        spacing=8,
    )

    grid = ft.Row(
        [
            ft.Container(card("Статусы", ft.Column([_hbar(type_dd, status_tf), chips_row], tight=True, spacing=10)), expand=2),
            ft.Container(card("Переходы", ft.Column([_hbar(from_dd, to_dd, cond_tf), trans_table, actions], spacing=10, tight=True)), expand=3),
        ],
        spacing=12,
    )
    return grid

# ----------------------------------- view -----------------------------------

def view(page: ft.Page) -> ft.View:
    # какая вкладка из query (tab=types/forms/routes)
    parsed = urlparse(page.route or "/blueprint/designer")
    qs = parse_qs(parsed.query or "")
    tab = (qs.get("tab", ["types"])[0] or "types").lower()
    tabs_map = {"types": 0, "forms": 1, "routes": 2}
    idx = tabs_map.get(tab, 0)

    tabs = ft.Tabs(
        selected_index=idx,
        animation_duration=150,
        tabs=[
            ft.Tab(text="Типы",   icon=ft.icons.CATEGORY, content=ft.Container(_tab_types(page), padding=0)),
            ft.Tab(text="Формы",  icon=ft.icons.DYNAMIC_FORM, content=ft.Container(_tab_forms(page), padding=0)),
            ft.Tab(text="Маршруты", icon=ft.icons.SCHEMA, content=ft.Container(_tab_routes(page), padding=0)),
        ],
        expand=False,
    )

    def _on_tab_change(_e: ft.ControlEvent) -> None:
        i = int(getattr(tabs, "selected_index", 0) or 0)
        rev = {v: k for k, v in tabs_map.items()}
        slug = rev.get(i, "types")
        page.go(f"/blueprint/designer?tab={slug}")

    tabs.on_change = _on_tab_change

    header = ft.Row(
        [
            ft.Text("Конструктор процессов", size=22, weight="w800"),
            ft.Container(expand=True),
            ft.OutlinedButton("К блюпринту", icon=ft.icons.ARROW_BACK, on_click=lambda _e: page.go("/blueprint")),
            ft.FilledButton("Сохранить конфигурацию", icon=ft.icons.SAVE, on_click=lambda _e: toast(page, "Черновик сохранён", kind="success")),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body = ft.Column([header, ft.Container(height=10), tabs], spacing=0, tight=True)
    return page_scaffold(page, title="Дизайнер", route="/blueprint/designer", body=body)
