from __future__ import annotations

import flet as ft

# ── helpers ──────────────────────────────────────────────────────────────────

def _alpha(color: str, a: float) -> str:
    """Безопасная прозрачность (на старых версиях Flet может не быть with_opacity)."""
    try:
        return ft.colors.with_opacity(a, color)
    except Exception:
        return color


def _icon(icon: str | None):
    """Строковый алиас и прямая передача иконки."""
    if isinstance(icon, str):
        return getattr(ft.icons, icon, None)
    return icon


def _tone_colors(tone: str) -> tuple[str, str]:
    """
    Возвращает пару (base, accent) для выбранного тона:
      - success | ok | green
      - warning | amber | orange
      - danger  | error | red
      - info (по умолчанию)
    """
    t = (tone or "info").lower()
    if t in ("success", "ok", "green"):
        return ft.colors.GREEN_700, ft.colors.GREEN_ACCENT_400
    if t in ("warning", "amber", "orange"):
        return ft.colors.AMBER_900, ft.colors.AMBER_ACCENT_400
    if t in ("danger", "error", "red"):
        return ft.colors.RED_700, ft.colors.RED_ACCENT_200
    # info / default
    return ft.colors.BLUE_GREY_900, ft.colors.BLUE_ACCENT_200


# ── Метрика / карточка ───────────────────────────────────────────────────────

def metric_tile(
    title: str,
    value: str | ft.Text,
    *,
    icon: str | None = None,
    tone: str = "info",
    width: float | None = 360,
    height: float | None = 96,
    expand: int | None = None,
    on_click=None,
) -> ft.Container:
    """
    Совместимая «плитка метрики»:
    - без MouseRegion / Transform / min_height (работает на старых Flet)
    - осторожные градиенты и тонкие рамки
    - кликабельность через on_click

    Аргументы:
      title  — заголовок
      value  — число/текст или готовый ft.Text
      tone   — info | success | warning | danger
      width  — ширина плитки (None = авто)
      height — высота плитки (None = авто)
      expand — можно передать 1, чтобы тянуться в строке
      on_click — обработчик клика
    """
    if not isinstance(value, ft.Text):
        value = ft.Text(str(value), size=22, weight="w800")

    icn = _icon(icon)
    base, accent = _tone_colors(tone)

    header = ft.Row(
        [
            ft.Icon(icn or ft.icons.INFO, size=18, opacity=0.9),
            ft.Text(title, size=12, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        spacing=8,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    content = ft.Column(
        [header, value],
        spacing=8,
        tight=True,
    )

    box = ft.Container(
        content=content,
        padding=14,
        width=width,
        height=height,
        expand=expand,
        border_radius=14,
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=[
                _alpha(base, 0.85),
                _alpha(base, 0.55),
                _alpha(accent, 0.25),
            ],
        ),
        border=ft.border.all(1, _alpha(ft.colors.WHITE, 0.06)),
        on_click=on_click,
    )
    return box


def stat_card(
    title: str,
    value: str | ft.Text,
    icon: str | None = None,
    tone: str = "info",
    *,
    width: float | None = None,
    height: float | None = 84,
    expand: int | None = None,
    on_click=None,
) -> ft.Container:
    """
    Компактная версия: по сути обёртка над metric_tile с меньшей высотой.
    """
    return metric_tile(
        title,
        value,
        icon=icon,
        tone=tone,
        width=width,
        height=height,
        expand=expand,
        on_click=on_click,
    )
