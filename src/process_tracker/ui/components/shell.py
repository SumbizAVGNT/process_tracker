# src/process_tracker/ui/components/shell.py
from __future__ import annotations

import flet as ft
from ..state import state

# ── helpers / compat ─────────────────────────────────────────────────────────
def _safe_color(name: str, fallback: str) -> str:
    return getattr(ft.colors, name, getattr(ft.colors, fallback, fallback))

def _alpha(color: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, color)
    except Exception:
        return color

# Градиент — берём из theme, если есть (мягкая зависимость)
try:
    from .theme import _alpha as theme_alpha, brand_gradient as theme_brand_gradient  # type: ignore
    def brand_gradient() -> ft.LinearGradient: return theme_brand_gradient()
    _alpha = theme_alpha  # type: ignore
except Exception:
    def brand_gradient() -> ft.LinearGradient:
        return ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[
                _alpha(_safe_color("BLUE_ACCENT_400", "BLUE"), 0.25),
                _alpha(_safe_color("PURPLE_ACCENT_200", "PURPLE"), 0.18),
            ],
        )

# Навбар — мягкая зависимость, есть запасной вариант
try:
    from .navbar import navbar  # type: ignore
except Exception:
    def navbar(page: ft.Page, active_route: str) -> ft.Container:
        items = [
            ("/dashboard", "Дашборд", getattr(ft.icons, "DASHBOARD", None) or getattr(ft.icons, "HOME", None)),
            ("/processes", "Процессы", getattr(ft.icons, "TIMELINE", None) or getattr(ft.icons, "LIST", None)),
            ("/tasks/create", "Создать задачу", getattr(ft.icons, "ADD_TASK", None) or getattr(ft.icons, "ADD", None)),
            ("/settings", "Настройки", getattr(ft.icons, "SETTINGS", None)),
        ]
        row = ft.Row(
            [ft.OutlinedButton(t, icon=i, on_click=lambda _e, r=r: page.go(r)) for r, t, i in items],
            spacing=10,
            wrap=False,
        )
        return ft.Container(row, padding=ft.padding.symmetric(8, 8))

MAX_W = 1200

# ── Topbar ───────────────────────────────────────────────────────────────────
def _topbar(page: ft.Page) -> ft.Container:
    user = state.user_email or "Гость"

    brand = ft.Row(
        [
            ft.Container(
                content=ft.Icon(getattr(ft.icons, "BOLT", None), size=18, color=_safe_color("BLUE_ACCENT_100", "BLUE")),
                width=36, height=36, border_radius=12,
                bgcolor=_alpha(_safe_color("BLUE_ACCENT_400", "BLUE"), 0.18),
                alignment=ft.alignment.center,
            ),
            ft.Text("Process Tracker", size=16, weight="w800"),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    right = ft.Row(
        [ft.Icon(getattr(ft.icons, "ACCOUNT_CIRCLE", None), size=18), ft.Text(user, weight="w600")],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        content=ft.Row([brand, ft.Container(expand=True), right],
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(14, 10),
        bgcolor=_alpha(_safe_color("SURFACE", "BLUE_GREY_900"), 0.04),
        border=ft.border.all(1, _alpha(_safe_color("ON_SURFACE", "WHITE"), 0.06)),
        border_radius=16,
    )

# ── Scaffold ─────────────────────────────────────────────────────────────────
def page_scaffold(
    page: ft.Page,
    *,
    title: str,
    route: str,
    body: ft.Control,
    show_topbar: bool = True,
    show_nav: bool = True,
    center: bool = False,
) -> ft.View:
    """
    Универсальный каркас страницы.
    - show_topbar / show_nav — вкл/выкл верхние панели
    - center=True — центрирует body по вертикали и горизонтали (для логина и т.п.)
    """
    # Базовые настройки страницы
    page.title = f"Процесс Трекер — {title}"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.colors.BLACK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    try:
        page.fonts = {"Inter": "https://rsms.me/inter/font-files/InterVariable.woff2"}
        page.theme = ft.Theme(font_family="Inter")
    except Exception:
        pass

    # Составляем «chrome»
    chrome_children: list[ft.Control] = []
    if show_topbar:
        chrome_children += [_topbar(page), ft.Container(height=10)]
    if show_nav:
        chrome_children += [navbar(page, route), ft.Container(height=10)]

    # Центровка контента
    if center:
        centered_slot = ft.Container(content=body, alignment=ft.alignment.center)
        content_area: ft.Control = ft.Column(
            [centered_slot],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    else:
        content_area = body

    chrome_children.append(content_area)

    chrome = ft.Container(
        content=ft.Column(
            chrome_children,
            spacing=0,
            tight=True,
            horizontal_alignment=(ft.CrossAxisAlignment.CENTER if center else ft.CrossAxisAlignment.START),
            alignment=(ft.MainAxisAlignment.CENTER if center else ft.MainAxisAlignment.START),
        ),
        width=MAX_W,
        padding=ft.padding.symmetric(18, 12),
    )

    # Корневой слой с градиентом и выравниванием
    root = ft.Container(
        expand=True,
        gradient=brand_gradient(),
        bgcolor=_alpha(_safe_color("ON_SURFACE", "WHITE"), 0.02),
        alignment=(ft.alignment.center if center else ft.alignment.top_center),
        content=chrome,
    )

    return ft.View(route=route, controls=[root])
