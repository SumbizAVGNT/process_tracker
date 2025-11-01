from __future__ import annotations
import datetime as dt
from typing import List, Optional

import flet as ft

from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..state import state
from ...core.logging import logger
from ..services.api import api


# ── helpers ──────────────────────────────────────────────────────────────────
def _alpha(c: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, c)
    except Exception:
        return c


def _opt(key: str, label: str) -> ft.dropdown.Option:
    return ft.dropdown.Option(key, label)


def _pretty_bytes(n: int | None) -> str:
    if not n:
        return "—"
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.0f} TB"


def _closable_chip(label: str, on_delete, *, height: int = 30) -> ft.Control:
    """
    Универсальный чип с крестиком:
    - Если есть ft.Chip и поддерживает on_delete — используем его
    - Иначе делаем свою «пилюлю» на Row
    """
    try:
        # у некоторых версий Flet Chip нет on_delete — проверим атрибут
        ch = ft.Chip(label=label)
        if hasattr(ch, "on_delete"):
            ch.on_delete = on_delete
            ch.delete_icon = ft.icons.CLOSE
            return ch
        # упадём в кастомный рендер ниже
    except Exception:
        pass

    # кастомная пилюля
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(label, size=12),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_size=14,
                    tooltip="Удалить",
                    on_click=lambda _e: on_delete(None),
                    style=ft.ButtonStyle(
                        padding=0,
                        shape=ft.RoundedRectangleBorder(radius=6),
                    ),
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        height=height,
        bgcolor=_alpha(ft.colors.SURFACE_VARIANT, 0.18),
        border=ft.border.all(1, _alpha(ft.colors.ON_SURFACE, 0.06)),
    )


# ── страница ─────────────────────────────────────────────────────────────────
def view(page: ft.Page) -> ft.View:
    logger.info("ui_task_create_open", route=page.route, user=state.user_email)

    # --------- поля ---------
    title = ft.TextField(
        label="Название задачи",
        hint_text="Короткое описание…",
        expand=True,
        dense=True,
    )

    description = ft.TextField(
        label="Описание задачи",
        hint_text="Детали, ожидания, как воспроизвести (если баг)…",
        multiline=True,
        min_lines=4,
        max_lines=10,
        dense=True,
    )

    type_dd = ft.Dropdown(
        label="Тип задачи",
        value="feature",
        options=[
            _opt("bug", "Баг"),
            _opt("feature", "Реализация"),
            _opt("procurement", "Закупка"),
            _opt("task", "Задача"),
            _opt("incident", "Инцидент"),
        ],
        dense=True,
        width=260,
    )

    priority_dd = ft.Dropdown(
        label="Важность",
        value="P2",
        options=[
            _opt("P0", "Срочно (P0)"),
            _opt("P1", "Ближайшее время (P1)"),
            _opt("P2", "Обычная (P2)"),
            _opt("P3", "Низкая (P3)"),
        ],
        dense=True,
        width=260,
    )

    # Исполнитель: пробуем подтянуть список, есть фоллбэк на email
    assignee_dd = ft.Dropdown(label="Исполнитель (список)", dense=True, width=320)
    assignee_email = ft.TextField(label="или укажите email исполнителя", dense=True, width=320)

    async def _load_users():
        try:
            users = await api.list_users()  # [{'id','name','email'}, ...]
            logger.info("ui_task_create_users_loaded", count=len(users))
            assignee_dd.options = [
                _opt(str(u.get("id", u.get("email", ""))), f"{u.get('name') or u.get('email')} ({u.get('email','')})")
                for u in (users or [])
            ]
            if assignee_dd.options:
                assignee_dd.value = assignee_dd.options[0].key
            try:
                assignee_dd.update()
            except Exception:
                pass
        except Exception as e:  # noqa: BLE001
            logger.warning("ui_task_create_users_failed", error=str(e))

    # Срок
    date_picker = ft.DatePicker()
    time_picker = ft.TimePicker()
    page.overlay.append(date_picker)
    page.overlay.append(time_picker)

    due_input = ft.TextField(
        label="Срок выполнения",
        hint_text="Выберите дату и время…",
        read_only=True,
        dense=True,
        width=260,
        prefix_icon=ft.icons.EVENT,
    )

    due_at: Optional[dt.datetime] = None

    def _format_due(d: Optional[dt.date], t: Optional[dt.time]) -> str:
        if not d:
            return ""
        if not t:
            return d.strftime("%d.%m.%Y")
        return dt.datetime.combine(d, t).strftime("%d.%m.%Y %H:%M")

    def _open_due_picker(_e=None):
        logger.info("ui_task_create_due_open")
        date_picker.pick_date()

    def _date_changed(_e):
        logger.info("ui_task_create_due_date_selected", date=str(date_picker.value))
        time_picker.pick_time()

    def _time_changed(_e):
        nonlocal due_at
        d: Optional[dt.date] = date_picker.value
        t: Optional[dt.time] = time_picker.value
        logger.info("ui_task_create_due_time_selected", time=str(t))
        if d:
            due_at = dt.datetime.combine(d, t or dt.time(18, 0))
            due_input.value = _format_due(d, t)
            try:
                due_input.update()
            except Exception:
                pass

    date_picker.on_change = _date_changed
    time_picker.on_change = _time_changed
    due_input.on_tap = _open_due_picker

    # Файлы / скриншоты
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    selected_files: List[ft.FilePickerFile] = []
    # ✅ заменили ft.Wrap на совместимый Row с переносом
    files_row = ft.Row(spacing=6, run_spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _refresh_files_ui():
        chips: List[ft.Control] = []
        for i, f in enumerate(selected_files):
            label = f"{f.name} · {_pretty_bytes(f.size)}"

            def _mk_remove(idx: int):
                return lambda _e=None: _remove_file(idx)

            chips.append(_closable_chip(label, on_delete=_mk_remove(i)))
        files_row.controls = chips
        try:
            files_row.update()
        except Exception:
            pass

    def _remove_file(idx: int):
        if 0 <= idx < len(selected_files):
            removed = selected_files.pop(idx)
            logger.info("ui_task_create_file_removed", name=removed.name, size=removed.size, path=removed.path)
            _refresh_files_ui()

    def _pick_files(_e=None):
        logger.info("ui_task_create_pick_files_open")
        file_picker.pick_files(allow_multiple=True)

    def _on_files_result(e: ft.FilePickerResultEvent):
        nonlocal selected_files
        if not e.files:
            logger.info("ui_task_create_pick_files_cancel")
            return
        selected_files.extend(e.files)
        logger.info(
            "ui_task_create_pick_files_done",
            count=len(e.files),
            names=[f.name for f in e.files],
        )
        _refresh_files_ui()

    file_picker.on_result = _on_files_result
    attach_btn = ft.OutlinedButton("Прикрепить файлы", icon=ft.icons.ATTACH_FILE, on_click=_pick_files)

    # предзагрузка пользователей (мягко)
    _ = page.run_task(_load_users) if hasattr(page, "run_task") else None

    # --------- сохранение ---------
    async def save():
        t = (title.value or "").strip()
        if not t:
            toast(page, "Введите название", kind="warning")
            logger.info("ui_task_create_submit_blocked", reason="empty_title")
            return

        payload = {
            "title": t,
            "description": (description.value or "").strip(),
            "type": type_dd.value,
            "priority": priority_dd.value,  # P0..P3
            "assignee": (assignee_email.value or "").strip() or assignee_dd.value,
            "due_at": (due_at.isoformat() if due_at else None),
        }
        logger.info("ui_task_create_submit", payload=payload, files=[f.name for f in selected_files])

        try:
            # 1) создаём задачу
            try:
                task = await api.create_task(**payload)  # type: ignore[arg-type]
            except TypeError:
                task = await api.create_task(t)  # старый API
            task_id = (task.get("id") if isinstance(task, dict) else None)

            # 2) загружаем файлы (desktop — по path; web — предупредим)
            uploaded = 0
            skipped_web = 0
            for f in selected_files:
                if not getattr(f, "path", None):
                    skipped_web += 1
                    logger.warning("ui_task_create_upload_skipped_web", name=f.name, size=f.size)
                    continue
                try:
                    if hasattr(api, "upload_file_path"):
                        await api.upload_file_path(task_id, f.path, name=f.name)  # type: ignore[arg-type]
                    elif hasattr(api, "upload_attachment"):
                        await api.upload_attachment(task_id, f.path, filename=f.name)  # type: ignore[arg-type]
                    else:
                        await api._req("POST", "/files", files={"file": f.path}, params={"task_id": task_id})  # type: ignore[attr-defined]
                    uploaded += 1
                    logger.info("ui_task_create_upload_done", name=f.name, size=f.size, path=f.path)
                except Exception as ex:  # noqa: BLE001
                    logger.error("ui_task_create_upload_failed", name=f.name, error=str(ex))

            if uploaded and skipped_web:
                toast(page, f"Задача создана, загружено файлов: {uploaded}. "
                            f"Файлы из браузера пока не прикреплены ({skipped_web}).", kind="success")
            else:
                toast(page, "Задача создана", kind="success")

            logger.info("ui_task_create_success", task_id=task_id, uploaded=uploaded, skipped_web=skipped_web)
            page.go("/dashboard")

        except Exception as ex:  # noqa: BLE001
            logger.error("ui_task_create_error", error=str(ex))
            toast(page, f"Ошибка: {ex}", kind="error")

    btn = async_button(page, "Создать", task_factory=save, icon=ft.icons.CHECK)

    # --------- разметка ---------
    header = ft.Row(
        [
            ft.Text("Создать задачу", size=20, weight="w800"),
            ft.Container(expand=True),
            ft.Icon(ft.icons.TASK_ALT_OUTLINED, opacity=0.7),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    meta_row = ft.Row(
        [
            type_dd,
            priority_dd,
            due_input,
        ],
        spacing=10,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )

    assignee_row = ft.Row(
        [assignee_dd, assignee_email],
        spacing=10,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )

    files_block = ft.Column(
        [
            ft.Row([attach_btn], alignment=ft.MainAxisAlignment.START),
            files_row,
            ft.Text(
                "Подсказка: в вебе Flet файл-путь недоступен, поэтому загрузка может быть ограничена. "
                "В desktop-режиме файлы прикрепятся автоматически.",
                size=11,
                color=ft.colors.ON_SURFACE_VARIANT,
            ),
        ],
        spacing=8,
        tight=True,
    )

    form = ft.Column(
        [
            header,
            ft.Divider(opacity=0.06),
            title,
            description,
            meta_row,
            assignee_row,
            ft.Container(height=8),
            files_block,
            ft.Container(height=8),
            ft.Row([btn], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=10,
        tight=True,
    )

    # аккуратная «стеклянная» карточка
    body = ft.Container(
        content=form,
        padding=16,
        border=ft.border.all(1, _alpha(ft.colors.ON_SURFACE, 0.06)),
        border_radius=16,
        bgcolor=_alpha(ft.colors.SURFACE, 0.05),
    )

    return page_scaffold(page, title="Создать задачу", route="/tasks/create", body=body)
