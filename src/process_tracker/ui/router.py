# src/process_tracker/ui/router.py

from __future__ import annotations

import flet as ft

from .pages.login import view as login_view
from .pages.dashboard import view as dashboard_view
from .pages.processes import view as processes_view
from .pages.settings import view as settings_view

# Маршруты приложения (UI)
ROUTES: dict[str, callable] = {
    "/": login_view,
    "/dashboard": dashboard_view,
    "/processes": processes_view,
    "/settings": settings_view,
}


def handle_route_change(page: ft.Page) -> None:
    """Простая маршрутизация: подменяем текущий View по адресу."""
    target = ROUTES.get(page.route, login_view)
    page.views.clear()
    page.views.append(target(page))
    page.update()
