from __future__ import annotations
import flet as ft
from typing import Optional, Sequence

# ── шымы под разные версии Flet ─────────────────────────────────────────────
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):  # pragma: no cover
    ft.icons = ft.Icons  # type: ignore[attr-defined]
if not hasattr(ft, "colors") and hasattr(ft, "Colors"):  # pragma: no cover
    ft.colors = ft.Colors  # type: ignore[attr-defined]
if not hasattr(ft, "alignment") and hasattr(ft, "Alignment"):  # pragma: no cover
    ft.alignment = ft.Alignment  # type: ignore[attr-defined]
if hasattr(ft, "colors") and not hasattr(ft.colors, "with_opacity"):  # pragma: no cover
    def _with_opacity(opacity: float, color: str) -> str: return color
    ft.colors.with_opacity = staticmethod(_with_opacity)  # type: ignore

# ── токены ───────────────────────────────────────────────────────────────────
RADIUS = 14
GAP = 12

def _color(attr: str, fallback: str) -> str:
    return getattr(ft.colors, attr, getattr(ft.colors, fallback, fallback))

SURFACE    = _color("SURFACE", "BLUE_GREY_900")
SURFACE_VAR= _color("SURFACE_VARIANT", "BLUE_GREY_700")
ON_SURF    = _color("ON_SURFACE", "WHITE")
ON_SURF_VAR= _color("ON_SURFACE_VARIANT", "GREY_500")
PRIMARY    = _color("BLUE_ACCENT_400", "BLUE")
PRIMARY_ALT= _color("PURPLE_ACCENT_200", "PURPLE")

def _alpha(color: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, color)
    except Exception:
        return color

def brand_gradient() -> ft.LinearGradient:
    return ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[_alpha(PRIMARY, 0.25), _alpha(PRIMARY_ALT, 0.18)],
    )

# ── стеклянная подложка ─────────────────────────────────────────────────────
def glass(
    content: ft.Control,
    *,
    padding: int | ft.PaddingValue = GAP,
    radius: int = RADIUS,
    bgcolor: Optional[str] = None,
    border_alpha: float = 0.08,
    surface_alpha: float = 0.06,
    shadow: bool = False,
    border: bool = True,
    width: float | int | None = None,
    height: float | int | None = None,
    on_click=None,
    tooltip: Optional[str] = None,
) -> ft.Container:
    box = ft.Container(
        content=content,
        padding=padding,
        width=width,
        height=height,
        bgcolor=bgcolor or _alpha(SURFACE, surface_alpha),
        border_radius=radius,
        ink=on_click is not None,
        on_click=on_click,
        tooltip=tooltip,
    )
    if border:
        box.border = ft.border.all(1, _alpha(ON_SURF, border_alpha))
    if shadow:
        box.shadow = ft.BoxShadow(
            blur_radius=16, spread_radius=1, color=_alpha(ft.colors.BLACK, 0.35), offset=ft.Offset(0, 6)
        )
    return box

# ── универсальная карточка ──────────────────────────────────────────────────
def _icon_value(icon: str | ft.Icon | None) -> Optional[str]:
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

def card(
    *args,
    icon: str | ft.Icon | None = None,
    actions: Optional[Sequence[ft.Control]] = None,
    padding: int | ft.PaddingValue = GAP,
    radius: int = RADIUS,
    **glass_kw,
) -> ft.Container:
    # режим 1: card(content)
    if len(args) == 1 and isinstance(args[0], ft.Control):
        return glass(args[0], padding=padding, radius=radius, **glass_kw)

    # режим 2: card(title, body, ...)
    title = args[0] if len(args) >= 1 else ""
    body  = args[1] if len(args) >= 2 and isinstance(args[1], ft.Control) else None

    header = ft.Row(
        [
            ft.Icon(_icon_value(icon), size=16) if icon else ft.Container(width=0),
            title if isinstance(title, ft.Control) else ft.Text(str(title), size=13, color=ON_SURF_VAR),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    children: list[ft.Control] = [header]
    if body is not None:
        children += [ft.Container(height=8), body]
    if actions:
        children += [ft.Container(height=8), ft.Row(list(actions), spacing=8, alignment=ft.MainAxisAlignment.END)]

    return glass(ft.Column(children, spacing=6, tight=True), padding=padding, radius=radius, **glass_kw)

# ── KPI ─────────────────────────────────────────────────────────────────────
def kpi(
    label: str,
    value: str | ft.Text | ft.Control,
    *,
    icon: str | ft.Icon | None = None,
    tone: str = "neutral",   # neutral | info | success | warning | error
    tooltip: Optional[str] = None,
    on_click=None,
) -> ft.Container:
    if not isinstance(value, ft.Control):
        value = ft.Text(str(value), size=22, weight="w800")

    tone_map = {
        "success": _color("GREEN_ACCENT_400", "GREEN"),
        "warning": _color("AMBER_ACCENT_200", "AMBER"),
        "error":   _color("RED_ACCENT_200", "RED"),
        "info":    _color("BLUE_ACCENT_400", "BLUE"),
        "neutral": SURFACE_VAR,
    }
    accent = tone_map.get(tone, SURFACE_VAR)

    row = ft.Row(
        [
            ft.Container(
                content=ft.Icon(_icon_value(icon) or _icon_value("INSIGHTS"), size=18),
                padding=10,
                border_radius=10,
                bgcolor=_alpha(accent, 0.16 if tone != "neutral" else 0.10),
            ),
            ft.Column([ft.Text(label, size=12, color=ON_SURF_VAR), value], spacing=4, tight=True),
        ],
        spacing=10, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return glass(row, padding=14, tooltip=tooltip, on_click=on_click)
