# src/process_tracker/ui/pages/settings.py

from __future__ import annotations

import flet as ft
from cryptography.fernet import Fernet
from sqlalchemy import select, text

from ..components.navbar import navbar
from ..components.forms import async_button, toast, confirm_dialog
from ...core.config import settings
from ...db.session import AsyncSessionLocal, engine


def _mask_db_url(url: str) -> str:
    # Маскируем пароль в URL: ...://user:***@host/...
    try:
        if "@" in url and "://" in url:
            head, tail = url.split("://", 1)
            creds_host = tail.split("@", 1)
            if len(creds_host) == 2:
                creds, host = creds_host
                if ":" in creds:
                    u, _p = creds.split(":", 1)
                    return f"{head}://{u}:***@{host}"
    except Exception:
        pass
    return url


def view(page: ft.Page) -> ft.View:
    page.title = "Процесс Трекер — настройки"

    # ---------- Шапка ----------
    title = ft.Text("Настройки", size=24, weight="bold")
    subtitle = ft.Text("Системные параметры и утилиты", color=ft.colors.ON_SURFACE_VARIANT)

    # ---------- Тема ----------
    def toggle_theme(_):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.update()

    theme_section = ft.Container(
        content=ft.Row(
            [
                ft.Text("Тема", size=16, weight="bold"),
                ft.Dropdown(
                    value="dark" if page.theme_mode == ft.ThemeMode.DARK else "light",
                    options=[ft.dropdown.Option("light"), ft.dropdown.Option("dark")],
                    on_change=lambda e: (
                        setattr(page, "theme_mode", ft.ThemeMode.DARK if e.control.value == "dark" else ft.ThemeMode.LIGHT),
                        page.update(),
                    ),
                    width=180,
                ),
                ft.IconButton(icon=ft.icons.BRIGHTNESS_6, tooltip="Переключить", on_click=toggle_theme),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=12,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.04, ft.colors.SURFACE_VARIANT),
    )

    # ---------- Конфиг / ENV ----------
    env_kv = [
        ("APP_ENV", settings.app_env),
        ("LOG_LEVEL", settings.log_level),
        ("API_HOST", settings.api_host),
        ("API_PORT", str(settings.api_port)),
        ("DB_URL", _mask_db_url(settings.db_url)),
    ]
    env_table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Ключ")), ft.DataColumn(ft.Text("Значение"))],
        rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(k)), ft.DataCell(ft.Text(v))]) for k, v in env_kv],
        column_spacing=24,
        data_row_min_height=32,
        horizontal_lines=ft.BorderSide(1, ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE)),
    )
    env_section = ft.Container(
        content=ft.Column(
            [ft.Text("Конфигурация", size=16, weight="bold"), env_table],
            spacing=10,
        ),
        padding=12,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.03, ft.colors.SURFACE_VARIANT),
    )

    # ---------- Утилиты ----------
    fernet_val = ft.TextField(label="Fernet key (сгенерированный, скопируй в .env → CRYPT_FERNET_KEY)", expand=True)
    copy_btn = ft.IconButton(
        icon=ft.icons.CONTENT_COPY,
        tooltip="Скопировать",
        on_click=lambda _: (page.set_clipboard(fernet_val.value or ""), toast(page, "Скопировано", kind="success")),
    )

    async def gen_fernet():
        fernet_val.value = Fernet.generate_key().decode()
        page.update()

    async def test_db():
        # Простая проверка соединения и базовой операции
        try:
            async with engine.begin() as conn:
                # SELECT 1; затем простой запрос текущей даты/времени
                await conn.execute(text("SELECT 1"))
            async with AsyncSessionLocal() as s:
                # Нейтральный ORM-запрос (безопасный, параметризованный)
                await s.execute(select(1))
            toast(page, "Соединение с БД — OK", kind="success")
        except Exception as e:  # noqa: BLE001
            toast(page, f"Ошибка БД: {e}", kind="error")

    async def rebuild_all():
        # ⚠️ Dev-утилита: пересоздание таблиц
        if await confirm_dialog(page, title="Пересоздать таблицы", text="Все данные будут удалены. Продолжить?"):
            from ...db import drop_db, init_db
            try:
                await drop_db()
                await init_db()
                toast(page, "Таблицы пересозданы", kind="success")
            except Exception as e:  # noqa: BLE001
                toast(page, f"Не удалось пересоздать: {e}", kind="error")

    key_tools = ft.Row(
        [
            fernet_val,
            copy_btn,
            async_button(page, "Сгенерировать ключ", task_factory=gen_fernet, icon=ft.icons.KEY),
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.END,
        spacing=10,
    )

    utils = ft.Column(
        [
            ft.Text("Утилиты", size=16, weight="bold"),
            key_tools,
            ft.Row(
                [
                    async_button(page, "Проверить БД", task_factory=test_db, icon=ft.icons.DATABASE),
                    async_button(
                        page,
                        "Пересоздать таблицы (dev)",
                        task_factory=rebuild_all,
                        icon=ft.icons.DELETE_SWEEP,
                        error_message="Не удалось пересоздать",
                    ),
                ],
                spacing=12,
            ),
        ],
        spacing=10,
    )

    utils_section = ft.Container(
        content=utils,
        padding=12,
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.03, ft.colors.SURFACE_VARIANT),
    )

    # ---------- Layout ----------
    content = ft.Column(
        [
            ft.Row([title], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            subtitle,
            ft.Divider(height=12, color="transparent"),
            theme_section,
            ft.Divider(height=12, color="transparent"),
            env_section,
            ft.Divider(height=12, color="transparent"),
            utils_section,
        ],
        expand=True,
        spacing=10,
    )

    return ft.View(
        route="/settings",
        controls=[
            navbar(page),
            ft.Container(content=content, padding=ft.padding.symmetric(16, 18), expand=True),
        ],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
