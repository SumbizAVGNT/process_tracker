"""
Набор переиспользуемых UI-компонентов для Flet:
- async_button(...)        — кнопка, которая безопасно выполняет async-задачу с лоадером
- confirm_dialog(...)      — модальное подтверждение, возвращает bool
- toast(page, msg, ...)    — снек-бар уведомления (info/success/warn/error)
- search_input(...)        — поле поиска с on_submit
- task_editor(...)         — мини-форма создания/редактирования задачи
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Callable, Awaitable, Optional

import flet as ft


# ----------------------------- Уведомления -----------------------------

def toast(
    page: ft.Page,
    message: str,
    *,
    kind: str = "info",
    duration: int = 2500,
) -> None:
    bg_map = {
        "info": ft.colors.BLUE_GREY_700,
        "success": ft.colors.GREEN_700,
        "warn": ft.colors.AMBER_700,
        "error": ft.colors.RED_700,
    }
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.colors.WHITE),
        bgcolor=bg_map.get(kind, ft.colors.BLUE_GREY_700),
        duration=duration,
        show_close_icon=True,
    )
    page.snack_bar.open = True
    page.update()


# ----------------------------- Диалог подтверждения -----------------------------

async def confirm_dialog(
    page: ft.Page,
    *,
    title: str = "Подтверждение",
    text: str = "Вы уверены?",
    ok_text: str = "Да",
    cancel_text: str = "Отмена",
) -> bool:
    result: dict[str, bool] = {"ok": False}

    def _on_ok(_):
        result["ok"] = True
        dlg.open = False
        page.update()

    def _on_cancel(_):
        result["ok"] = False
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight="bold"),
        content=ft.Text(text),
        actions=[
            ft.TextButton(cancel_text, on_click=_on_cancel),
            ft.FilledButton(ok_text, on_click=_on_ok),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = dlg
    dlg.open = True
    page.update()

    while dlg.open:
        await ft.asyncio.sleep(0.05)

    return result["ok"]


# ----------------------------- Асинхронная кнопка -----------------------------

def async_button(
    page: ft.Page,
    label: str,
    *,
    task_factory: Callable[[], Awaitable[None]],
    icon: Optional[str] = None,
    tooltip: Optional[str] = None,
    success_message: Optional[str] = None,
    error_message: str = "Ошибка выполнения",
    width: Optional[int] = None,
) -> ft.Container:
    loader = ft.ProgressRing(visible=False, width=18, height=18)
    btn = ft.FilledButton(
        text=label,
        icon=icon,
        tooltip=tooltip,
        disabled=False,
        width=width,
    )

    async def _run():
        try:
            btn.disabled = True
            loader.visible = True
            btn.update()
            loader.update()
            await task_factory()
            if success_message:
                toast(page, success_message, kind="success")
        except Exception as e:  # noqa: BLE001
            toast(page, f"{error_message}: {e}", kind="error")
        finally:
            btn.disabled = False
            loader.visible = False
            btn.update()
            loader.update()

    # ВАЖНО: передаём функцию, без вызова
    btn.on_click = lambda _: page.run_task(_run)

    return ft.Container(
        content=ft.Row(
            [btn, loader],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


# ----------------------------- Поле поиска -----------------------------

def search_input(
    page: ft.Page,
    *,
    placeholder: str = "Поиск…",
    on_submit: Callable[[str], Awaitable[None]] | Callable[[str], None],
    width: int | None = 360,
    autofocus: bool = False,
) -> ft.TextField:
    tf = ft.TextField(
        hint_text=placeholder,
        autofocus=autofocus,
        width=width,
        prefix_icon=ft.icons.SEARCH,
        dense=True,
    )

    def _submit(_):
        q = (tf.value or "").strip()
        if not q:
            return
        res = on_submit(q)
        # Если вернулась корутина — запустим её безопасно
        if inspect.iscoroutine(res):
            asyncio.create_task(res)

    tf.on_submit = _submit
    return tf


# ----------------------------- Редактор задачи -----------------------------

def task_editor(
    page: ft.Page,
    *,
    on_save: Callable[[str], Awaitable[None]],
    label: str = "Новая задача",
    button_text: str = "Добавить",
) -> ft.Container:
    title = ft.TextField(label=label, expand=True)
    add_btn = async_button(
        page,
        button_text,
        task_factory=lambda: on_save((title.value or "").strip()),
        icon=ft.icons.ADD,
        success_message="Задача добавлена",
        error_message="Не удалось добавить задачу",
    )

    return ft.Container(
        content=ft.Row(
            [title, add_btn],
            vertical_alignment=ft.CrossAxisAlignment.END,
            spacing=10,
        )
    )
