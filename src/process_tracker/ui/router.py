from __future__ import annotations

import flet as ft

from .state import state


# ---- Маршруты и ленивые фабрики страниц ------------------------------------
def _resolve_view(page: ft.Page, route: str) -> ft.View:
    """
    Возвращает ft.View по запрошенному маршруту.
    Все импорты страниц ленивые, чтобы не тянуть лишнее при старте.
    """
    # Гард: неавторизованных на /login
    protected = {"/dashboard", "/processes", "/settings", "/tasks/create"}
    if route in protected and not state.is_authenticated:
        route = "/"

    if route in ("/", "/login"):
        from .pages import login as _login

        return _login.view(page)

    if route == "/dashboard":
        from .pages import dashboard as _dashboard

        return _dashboard.view(page)

    if route == "/processes":
        from .pages import processes as _proc

        return _proc.view(page)

    if route == "/settings":
        from .pages import settings as _settings

        return _settings.view(page)

    if route == "/tasks/create":
        from .pages import task_create as _tc

        return _tc.view(page)

    # 404 — простая stub-страница
    return ft.View(
        route="/404",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Страница не найдена", size=22, weight="w700"),
                        ft.Text(f"Маршрут: {route}", color=ft.colors.ON_SURFACE_VARIANT),
                        ft.FilledButton("На главную", icon=ft.icons.HOME, on_click=lambda _: page.go("/")),
                    ],
                    spacing=10,
                ),
                padding=20,
                expand=True,
                alignment=ft.alignment.center,
            )
        ],
    )


# ---- Переходы ---------------------------------------------------------------
def handle_route_change(page: ft.Page) -> None:
    """
    Главный роутер приложения.
    Минимизируем «дёргание»: собираем view полностью и одним присваиванием меняем page.views.
    """
    try:
        target_route = page.route or "/"
        target_view = _resolve_view(page, target_route)

        # одно обновление вместо серии .append()/.update()
        page.views[:] = [target_view]
        page.update()
    except Exception as e:  # noqa: BLE001
        # Аварийный fallback на 500
        page.views[:] = [
            ft.View(
                route="/500",
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Ошибка интерфейса", size=22, weight="w700"),
                                ft.Text(str(e), color=ft.colors.ON_SURFACE_VARIANT),
                                ft.FilledButton("Обновить", icon=ft.icons.REFRESH, on_click=lambda _: page.go(page.route or "/")),
                            ],
                            spacing=10,
                        ),
                        padding=20,
                        expand=True,
                        alignment=ft.alignment.center,
                    )
                ],
            )
        ]
        page.update()
