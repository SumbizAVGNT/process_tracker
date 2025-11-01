from __future__ import annotations
import flet as ft

def attach_hotkeys(page: ft.Page) -> None:
    # защита от повторной регистрации
    if getattr(page, "_hotkeys_attached", False):
        return
    setattr(page, "_hotkeys_attached", True)  # type: ignore[attr-defined]

    async def _open_palette():
        try:
            from .components.command_palette import show_command_palette
        except Exception:
            return
        cmds = [
            {"label": "Открыть дашборд",  "icon": "DASHBOARD", "action": lambda: page.go("/dashboard")},
            {"label": "Процессы",        "icon": "TIMELINE",  "action": lambda: page.go("/processes")},
            {"label": "Создать задачу",  "icon": "ADD",       "action": lambda: _quick_create()},
            {"label": "Настройки",       "icon": "SETTINGS",  "action": lambda: page.go("/settings")},
            {"label": "Выйти",           "icon": "LOGOUT",    "action": lambda: page.go("/")},
        ]
        await show_command_palette(page, cmds)

    async def _quick_create():
        try:
            from .components.quick_create import open_quick_create
            await open_quick_create(page)
        except Exception:
            pass

    def _on_key(e: ft.KeyboardEvent) -> None:
        key = (e.key or "").lower()
        ctrl = bool(e.ctrl or e.meta)
        alt  = bool(e.alt)

        if ctrl and key == "k":
            if hasattr(page, "run_task"):
                page.run_task(_open_palette)  # type: ignore[attr-defined]
        elif alt and key == "n":
            if hasattr(page, "run_task"):
                page.run_task(_quick_create)  # type: ignore[attr-defined]
        elif key == "/":
            # попытаться сфокусировать глобальный поиск (если появится)
            try:
                if hasattr(page, "_global_search"):           # type: ignore[attr-defined]
                    page._global_search.focus()               # type: ignore[attr-defined]
                    page.update()
            except Exception:
                pass

    page.on_keyboard_event = _on_key
