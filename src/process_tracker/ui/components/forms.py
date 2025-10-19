# src/process_tracker/ui/components/forms.py
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

import asyncio
import flet as ft

# Совместимость с разными версиями Flet: icons/Icons
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]

# ============================ helpers ============================

def _icon_value(icon: str | ft.Icon | None) -> str | None:
    """
    Нормализация иконок:
      - "ADD" / "LOGIN" → ft.icons.ADD / "add"
      - "add" (готовая строка)
      - ft.icons.ADD
      - ft.Icon(name="add")
    Возвращает строковое имя иконки или None.
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


def _alpha(color: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, color)
    except Exception:
        return color


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
        def __init__(self, text: str, icon: Optional[str | ft.Icon] = None):
            norm_icon = _icon_value(icon)
            super().__init__(text, icon=norm_icon)
            self._loading_overlay = ft.ProgressRing(visible=False, width=16, height=16)
            self.content = ft.Row(
                [ft.Icon(norm_icon) if norm_icon else ft.Container(width=0), ft.Text(text), self._loading_overlay],
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
    surf_variant = getattr(ft.colors, "SURFACE_VARIANT", getattr(ft.colors, "BLUE_GREY_700", ft.colors.GREY_700))

    if kind == "success":
        icon = _icon_value("CHECK_CIRCLE")
        bgcolor = _alpha(ft.colors.GREEN, 0.12)
    elif kind in ("warn", "warning"):
        icon = _icon_value("WARNING_AMBER") or _icon_value("WARNING")
        bgcolor = _alpha(ft.colors.AMBER, 0.12)
    elif kind in ("error", "danger"):
        icon = _icon_value("ERROR_OUTLINE") or _icon_value("ERROR")
        bgcolor = _alpha(ft.colors.RED, 0.12)
    else:  # info
        icon = _icon_value("INFO")
        bgcolor = _alpha(surf_variant, 0.12)

    content = ft.Row(
        [ft.Icon(icon, size=18) if icon else ft.Container(width=0), ft.Text(message)],
        spacing=10,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.snack_bar = ft.SnackBar(
        content=content,
        open=True,
        bgcolor=bgcolor,
        duration=duration_ms,
        show_close_icon=True,
        behavior=getattr(ft, "SnackBarBehavior", object).__dict__.get("FLOATING", None),
        dismiss_direction=getattr(ft, "DismissDirection", object).__dict__.get("DOWN", None),
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
    icon: str | ft.Icon | None = None,
    disabled: bool = False,
    expand: int | bool | None = None,
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
                page.run_task(_run)  # Flet ожидает корутинную функцию
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
            # Крайний случай: без loop и без page.run_task — выполняем блокирующе
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
            ft.FilledButton(ok_text, icon=_icon_value("CHECK"), on_click=lambda _e: _finish(True)),
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
    # Используем ваш TextField, если доступен, иначе Flet
    if TextField is object:
        name = ft.TextField(
            label=label,
            hint_text="Введите название…",
            expand=True,
            width=width,
            dense=True,
        )
    else:
        name = TextField(label, hint_text="Введите название…", expand=True, width=width, dense=True)  # type: ignore

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
        icon=_icon_value("ADD"),
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
