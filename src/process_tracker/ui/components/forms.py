# src/process_tracker/ui/components/forms.py
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

import asyncio
import flet as ft

# Совместимость с разными версиями Flet: icons/Icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

# Если у вас есть собственные поля / формы — они могут отсутствовать на раннем этапе.
# Импорты сделаны опциональными, чтобы модуль работал даже без них.
try:
    from .dynamic_form import DynamicForm, build_schema_fields  # type: ignore
except Exception:  # pragma: no cover
    DynamicForm = object  # type: ignore
    def build_schema_fields(*_a, **_kw):  # type: ignore
        return []

try:
    from .form_field import TextField, EmailField, IntegerField  # type: ignore
except Exception:  # pragma: no cover
    TextField = EmailField = IntegerField = object  # type: ignore

try:
    from .password_field import PasswordField  # type: ignore
except Exception:  # pragma: no cover
    PasswordField = object  # type: ignore

try:
    from .button import LoadingButton  # type: ignore
except Exception:  # pragma: no cover
    class LoadingButton(ft.FilledButton):  # минимальный fallback
        def __init__(self, text: str, icon: Optional[str] = None):
            super().__init__(text, icon=icon)
            self._loading_overlay = ft.ProgressRing(visible=False, width=16, height=16)
            self.content = ft.Row(
                [ft.Icon(icon) if icon else ft.Container(width=0), ft.Text(text), self._loading_overlay],
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def set_loading(self, v: bool) -> None:
            self.disabled = v
            self._loading_overlay.visible = v
            try:
                self.update()
            except Exception:
                pass


# --------------------------- УВЕДОМЛЕНИЯ (toast) ---------------------------

def toast(
    page: ft.Page,
    message: str,
    *,
    kind: str = "info",  # "info" | "success" | "warning" | "error"
    duration_ms: int = 2500,
) -> None:
    """Быстрое уведомление внизу страницы."""
    kind = (kind or "info").lower()
    if kind == "success":
        icon = getattr(ft.icons, "CHECK_CIRCLE", None)
        bgcolor = ft.colors.with_opacity(0.12, ft.colors.GREEN)
    elif kind in ("warn", "warning"):
        icon = getattr(ft.icons, "WARNING_AMBER", None) or getattr(ft.icons, "WARNING", None)
        bgcolor = ft.colors.with_opacity(0.12, ft.colors.AMBER)
    elif kind in ("error", "danger"):
        icon = getattr(ft.icons, "ERROR_OUTLINE", None) or getattr(ft.icons, "ERROR", None)
        bgcolor = ft.colors.with_opacity(0.12, ft.colors.RED)
    else:  # info
        icon = getattr(ft.icons, "INFO", None)
        bgcolor = ft.colors.with_opacity(0.12, ft.colors.SURFACE_VARIANT)

    content = ft.Row(
        [ft.Icon(icon, size=18), ft.Text(message)],
        spacing=10,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.snack_bar = ft.SnackBar(
        content=content,
        open=True,
        bgcolor=bgcolor,
        duration=duration_ms,
        dismiss_direction=ft.DismissDirection.DOWN,
        show_close_icon=True,
        behavior=ft.SnackBarBehavior.FLOATING,
    )
    page.update()


# ---------------------- КНОПКА С ASYNC-ОБРАБОТЧИКОМ ----------------------

def async_button(
    page: ft.Page | None,
    text: str,
    *,
    # два способа: либо фабрика корутины без события, либо обработчик с событием
    task_factory: Callable[[], Awaitable[Any]] | None = None,
    on_click_async: Callable[[ft.ControlEvent], Awaitable[Any]] | None = None,
    icon: str | None = None,
    disabled: bool = False,
    expand: int | None = None,
    width: float | None = None,
    tooltip: str | None = None,
    **button_kwargs: Any,
) -> LoadingButton:
    """
    Кнопка, которая выполняет async-обработчик без блокировки UI.

    Примеры:
        # 1) Через фабрику задачи (без e)
        btn = async_button(page, "Войти", task_factory=lambda: do_login())

        # 2) Через обработчик события с e
        btn = async_button(page, "Сохранить", on_click_async=handle_submit)

    При исключении покажет toast(error) если передана page.
    """
    if task_factory is None and on_click_async is None:
        raise ValueError("async_button: укажите task_factory= или on_click_async=")

    btn = LoadingButton(text, icon=icon)
    btn.disabled = disabled
    if expand is not None:
        btn.expand = expand
    if width is not None:
        btn.width = width
    if tooltip is not None:
        btn.tooltip = tooltip

    # Прокинуть остальные поддерживаемые атрибуты Flet-кнопки
    for k, v in button_kwargs.items():
        try:
            setattr(btn, k, v)
        except Exception:
            pass

    def _handler(e: ft.ControlEvent) -> None:
        async def _run():
            btn.set_loading(True)
            try:
                if task_factory is not None:
                    await task_factory()
                elif on_click_async is not None:
                    await on_click_async(e)
            except Exception as err:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                if page is not None:
                    toast(page, str(err), kind="error")
            finally:
                btn.set_loading(False)

        # безопасное планирование выполнения корутины
        scheduled = False
        if page is not None and hasattr(page, "run_task"):
            try:
                # Flet API: ожидает корутинную ФУНКЦИЮ, не объект
                page.run_task(_run)
                scheduled = True
            except Exception:
                scheduled = False

        if not scheduled:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run(), name="async_button")
                scheduled = True
            except RuntimeError:
                scheduled = False

        if not scheduled:
            # Крайний случай: синхронный поток без loop и без page.run_task
            # Выполним корутину блокирующе, чтобы не терять действие.
            asyncio.run(_run())

    btn.on_click = _handler
    return btn


# ---------------------- МОДАЛЬНОЕ ПОДТВЕРЖДЕНИЕ ----------------------

async def confirm_dialog(
    page: ft.Page,
    *,
    title: str = "Подтверждение",
    text: str = "Вы уверены?",
    ok_text: str = "Да",
    cancel_text: str = "Отмена",
) -> bool:
    """
    Открывает модальное подтверждение и возвращает True/False.
    Использует Future, чтобы удобно awaited-ить из любых мест.
    """
    loop = asyncio.get_running_loop()
    fut: asyncio.Future[bool] = loop.create_future()

    def _finish(value: bool) -> None:
        dlg.open = False
        page.update()
        if not fut.done():
            fut.set_result(value)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight="w600"),
        content=ft.Text(text),
        actions=[
            ft.TextButton(cancel_text, on_click=lambda _e: _finish(False)),
            ft.FilledButton(ok_text, icon=ft.icons.CHECK, on_click=lambda _e: _finish(True)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.dialog = dlg
    dlg.open = True
    page.update()
    return await fut


# ---------------------- ПРОСТОЙ РЕДАКТОР ЗАДАЧИ ----------------------

def task_editor(
    page: ft.Page,
    *,
    on_save: Callable[[str], Awaitable[Any]],
    label: str = "Новая задача",
    button_text: str = "Добавить",
    width: Optional[float] = None,
) -> ft.Row:
    """
    Лёгкий инлайн-редактор: поле + кнопка «Добавить».
    Использование в страницах (см. /ui/pages/processes.py):
        editor = task_editor(page, on_save=add_task_handler, label="Новая задача")
    """
    name = ft.TextField(
        label=label,
        hint_text="Введите название…",
        expand=True,
        width=width,
        dense=True,
    )

    # Enter в поле — тоже сохранить
    def _on_submit(_e: ft.ControlEvent) -> None:
        async def _go():
            title = (name.value or "").strip()
            if not title:
                toast(page, "Название не должно быть пустым", kind="warning")
                return
            await on_save(title)
            name.value = ""
            try:
                name.update()
            except Exception:
                pass

        # безопасное планирование
        if hasattr(page, "run_task"):
            page.run_task(_go)
        else:
            try:
                asyncio.get_running_loop().create_task(_go(), name="task_editor_submit")
            except RuntimeError:
                asyncio.run(_go())

    name.on_submit = _on_submit

    add_btn = async_button(
        page,
        button_text,
        task_factory=lambda: on_save((name.value or "").strip()),
        icon=ft.icons.ADD,
        tooltip="Сохранить",
    )

    return ft.Row(
        [name, add_btn],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )


__all__ = [
    # формы и поля (если доступны)
    "DynamicForm",
    "build_schema_fields",
    "TextField",
    "EmailField",
    "IntegerField",
    "PasswordField",
    # вспомогательные утилиты
    "async_button",
    "toast",
    "confirm_dialog",
    "task_editor",
]
