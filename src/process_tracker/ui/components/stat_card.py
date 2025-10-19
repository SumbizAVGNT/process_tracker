from __future__ import annotations
from typing import Any, Iterable
import flet as ft


# ── helpers ──────────────────────────────────────────────────────────────────
def _icon_value(icon: str | ft.Icon | None) -> str | None:
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

def _color(attr: str, fallback: str) -> str:
    return getattr(ft.colors, attr, getattr(ft.colors, fallback, fallback))


# ── micro-sparkline (мини-тренд) ─────────────────────────────────────────────
def _sparkline(values: Iterable[float] | None, *, color: str) -> ft.Control:
    vals = list(values or [])
    if not vals:
        return ft.Container(height=0)
    mx = max(vals) or 1
    bars: list[ft.Control] = []
    for v in vals:
        h = 26 * (float(v) / mx)
        bars.append(ft.Container(width=4, height=max(2, h), bgcolor=_alpha(color, 0.55), border_radius=3))
    return ft.Row(bars, spacing=3, vertical_alignment=ft.CrossAxisAlignment.END)


# ── main: неон-гласс плитка ──────────────────────────────────────────────────
def metric_tile(
    title: str,
    value: Any,
    *,
    icon: str | ft.Icon | None = None,
    tone: str = "info",        # info | success | warning | error | neutral
    trend: Iterable[float] | None = None,
    tooltip: str | None = None,
    on_click=None,
) -> ft.Container:
    # палитра
    surf = _color("SURFACE", "BLUE_GREY_900")
    on_var = _color("ON_SURFACE_VARIANT", "GREY_500")
    tone_map = {
        "success": _color("GREEN_ACCENT_400", "GREEN"),
        "warning": _color("AMBER_ACCENT_200", "AMBER"),
        "error":   _color("RED_ACCENT_200", "RED"),
        "info":    _color("BLUE_ACCENT_400", "BLUE"),
        "neutral": _color("BLUE_GREY_600", "BLUE_GREY_600"),
    }
    accent = tone_map.get(tone, tone_map["info"])

    # значение
    val_ctl = value if isinstance(value, ft.Control) else ft.Text(str(value), size=28, weight="w800")

    pill = ft.Container(
        content=ft.Icon(_icon_value(icon) or _icon_value("INSIGHTS"), size=18, color=_alpha(ft.colors.WHITE, 0.92)),
        padding=10,
        border_radius=12,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=[_alpha(accent, 0.30), _alpha(accent, 0.16)],
        ),
        border=ft.border.all(1, _alpha(accent, 0.25)),
    )

    content = ft.Column(
        [
            ft.Row([pill, ft.Text(title, size=13, color=on_var)],
                   spacing=10, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            val_ctl,
            _sparkline(trend, color=accent),
        ],
        spacing=10,
        tight=True,
    )

    inner = ft.Container(
        content=content,
        padding=18,
        border_radius=18,
        bgcolor=_alpha(surf, 0.06),
    )

    tile = ft.Container(
        padding=1.2,
        border_radius=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=[_alpha(accent, 0.55), _alpha(accent, 0.10)],
        ),
        shadow=ft.BoxShadow(
            blur_radius=22, spread_radius=0, color=_alpha(ft.colors.BLACK, 0.40), offset=ft.Offset(0, 8)
        ),
        tooltip=tooltip,
        ink=on_click is not None,
        on_click=on_click,
        content=inner,
    )

    # ── hover-эффект с учётом версии Flet ────────────────────────────────────
    HAS_TRANSFORM = hasattr(ft, "Transform") and hasattr(tile, "animate_scale")

    if HAS_TRANSFORM:
        # Новые версии: используем transform scale-анимацию
        tile.transform = ft.Transform(scale=1.0)           # type: ignore[attr-defined]
        tile.animate_scale = ft.Animation(180, "easeOut")  # type: ignore[attr-defined]
        inner.animate_opacity = ft.Animation(150, "easeOut")

        def _hover(e: ft.HoverEvent):
            hovered = e.data == "true"
            tile.transform = ft.Transform(scale=1.02 if hovered else 1.0)  # type: ignore[attr-defined]
            inner.opacity = 0.96 if hovered else 1.0
            inner.bgcolor = _alpha(surf, 0.09 if hovered else 0.06)
            try: tile.update()
            except Exception: pass
    else:
        # Старые версии: без Transform — меняем тень и прозрачность
        inner.animate_opacity = ft.Animation(150, "easeOut")

        def _hover(e: ft.HoverEvent):
            hovered = e.data == "true"
            inner.opacity = 0.96 if hovered else 1.0
            inner.bgcolor = _alpha(surf, 0.09 if hovered else 0.06)
            tile.shadow = ft.BoxShadow(
                blur_radius=26 if hovered else 22,
                spread_radius=0,
                color=_alpha(ft.colors.BLACK, 0.42 if hovered else 0.40),
                offset=ft.Offset(0, 10 if hovered else 8),
            )
            try: tile.update()
            except Exception: pass

    tile.on_hover = _hover
    return tile


# совместимость со старым API
def stat_card(title: str, value: Any, icon: str | None = None, **kw) -> ft.Container:
    return metric_tile(title, value, icon=icon, **kw)
