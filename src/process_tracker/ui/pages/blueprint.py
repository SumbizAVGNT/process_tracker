# src/process_tracker/ui/pages/blueprint.py
from __future__ import annotations
import flet as ft

from ..components.shell import page_scaffold


# ── helpers ──────────────────────────────────────────────────────────────────
def _alpha(c: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, c)
    except Exception:
        return c


def _icon(name: str):
    return getattr(ft.icons, name, None)


def _section_card(
    title: str,
    bullets: list[str],
    *,
    icon=None,
    actions: list[ft.Control] | None = None,
) -> ft.Container:
    head = ft.Row(
        [
            ft.Icon(icon or _icon("AUTO_AWESOME"), size=16),
            ft.Text(title, size=13, color=ft.colors.ON_SURFACE_VARIANT),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    items = ft.Column(
        [
            ft.Row(
                [ft.Icon(_icon("CHECK_CIRCLE_OUTLINE"), size=14, opacity=0.9), ft.Text(b, selectable=True)],
                spacing=8,
            )
            for b in bullets
        ],
        spacing=6,
        tight=True,
    )

    col = ft.Column([head, ft.Container(height=8), items], spacing=0, tight=True)
    if actions:
        col.controls += [
            ft.Container(height=8),
            ft.Row(actions, alignment=ft.MainAxisAlignment.END, spacing=8),
        ]

    return ft.Container(
        content=col,
        padding=14,
        border_radius=14,
        bgcolor=_alpha(ft.colors.SURFACE, 0.06),
        border=ft.border.all(1, _alpha(ft.colors.ON_SURFACE, 0.06)),
    )


def _grid(cards: list[ft.Control]) -> ft.Row:
    # Совместимая сетка: перенос по рядам без ResponsiveRow
    tile_w = 440
    return ft.Row(
        [ft.Container(c, width=tile_w) for c in cards],
        spacing=12,
        run_spacing=12,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


# ── контент вкладок ──────────────────────────────────────────────────────────
def _tab1(page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "Гибкость и настраиваемость",
                [
                    "Конструктор процессов без кода (формы, статусы, роли).",
                    "Разные типы процессов с собственными полями и правилами.",
                    "Ветвления/параллельные этапы/условия в маршрутах.",
                ],
                icon=_icon("BUILD_CIRCLE_OUTLINED"),
                actions=[
                    ft.FilledButton(
                        "Конструктор форм",
                        icon=_icon("DYNAMIC_FORM"),
                        on_click=lambda _e: page.go("/blueprint/designer?tab=forms"),
                    ),
                    ft.OutlinedButton(
                        "Статусы и роли",
                        icon=_icon("ADMIN_PANEL_SETTINGS"),
                        # в дизайнере это вторая вкладка; параметр ожидается как "types"
                        on_click=lambda _e: page.go("/blueprint/designer?tab=types"),
                    ),
                    ft.OutlinedButton(
                        "Маршруты",
                        icon=_icon("SCHEMA"),
                        on_click=lambda _e: page.go("/blueprint/designer?tab=routes"),
                    ),
                ],
            ),
            _section_card(
                "Права доступа (RBAC)",
                [
                    "Тонкие разрешения: читать/создавать/редактировать/удалять.",
                    "Группы/роли + маски вроде task.* и admin.*.",
                ],
                icon=_icon("ADMIN_PANEL_SETTINGS_OUTLINED"),
                actions=[
                    ft.OutlinedButton(
                        "Матрица прав",
                        icon=_icon("GRID_ON"),
                        # открываем вкладку матрицы (в дизайнере это тот же ?tab=types)
                        on_click=lambda _e: page.go("/blueprint/designer?tab=types"),
                    )
                ],
            ),
            _section_card(
                "API-first и интеграции",
                [
                    "REST API и webhooks для событий.",
                    "Мессенджеры (Slack/Teams), Drive/Confluence/Notion.",
                    "GitHub/GitLab/Jira/мониторинг/CRM/ERP/BI.",
                ],
                icon=_icon("SYNC_ALT"),
                actions=[
                    ft.OutlinedButton(
                        "Открыть API",
                        icon=_icon("ROCKET_LAUNCH"),
                        on_click=lambda _e: page.go("/settings"),  # временно ведём в настройки/интеграции
                    )
                ],
            ),
            _section_card(
                "Производительность и надёжность",
                [
                    "Горизонтальное масштабирование, очереди, кэш.",
                    "Минимальные простои, миграции без простоев.",
                ],
                icon=_icon("SPEED"),
            ),
        ]
    )


def _tab2(_page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "Глубокая связь с кодом",
                [
                    "Линки на коммиты/ветки/PR прямо из задач.",
                    "Автоматические статусы CI/CD в карточке задачи.",
                ],
                icon=_icon("CODE"),
            ),
            _section_card(
                "Шаблоны IT-workflow",
                [
                    "Баги/фичи/инциденты/рефакторинг — готовые конфигурации.",
                    "Поля ‘среда’, ‘версия’, ‘компонент’.",
                ],
                icon=_icon("INTEGRATION_INSTRUCTIONS"),
            ),
            _section_card(
                "Инциденты и SLA",
                [
                    "Приоритизация P0–P2, таймеры реакции/решения.",
                    "Постмортем — шаблон и артефакты расследования.",
                ],
                icon=_icon("EMERGENCY"),
            ),
        ]
    )


def _tab3(_page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "Визуальные конструкторы (No-Code)",
                [
                    "Рисуем блок-схему — получаем маршрут и формы.",
                    "Ветвления и условия доступны аналитикам.",
                ],
                icon=_icon("SCHEMA"),
            ),
            _section_card(
                "Формы и сбор данных",
                [
                    "Валидаторы, справочники, зависимости полей.",
                    "Импорт/экспорт, дубликаты, маски ввода.",
                ],
                icon=_icon("DYNAMIC_FORM"),
            ),
            _section_card(
                "BI и метрики",
                [
                    "KPI: время цикла, загрузка, bottlenecks.",
                    "Экспорт в Power BI/Tableau, встроенные отчёты.",
                ],
                icon=_icon("ANALYTICS"),
            ),
        ]
    )


def _tab4(_page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "Коммуникации",
                [
                    "Комментарии, треды, @упоминания.",
                    "Q&A внутри задачи — не смешивается с логом действий.",
                ],
                icon=_icon("MODE_COMMENT_OUTLINED"),
            ),
            _section_card(
                "Уведомления и эскалации",
                [
                    "Гибкие правила, чтобы не спамить.",
                    "Эскалации по таймерам/условиям.",
                ],
                icon=_icon("NOTIFICATIONS_ACTIVE_OUTLINED"),
            ),
            _section_card(
                "Файлы и история",
                [
                    "Вложения с версиями, предпросмотр.",
                    "Полный аудит изменений в карточке.",
                ],
                icon=_icon("ATTACH_FILE"),
            ),
        ]
    )


def _tab5(_page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "Интерфейс класса Linear",
                [
                    "Скорость, минимум отвлекающих элементов.",
                    "Горячие клавиши, быстрые действия, командная палитра.",
                ],
                icon=_icon("ROCKET_LAUNCH_OUTLINED"),
            ),
            _section_card(
                "Поиск и фильтры",
                [
                    "Глобальный поиск, сохранённые вьюхи (‘Мои баги’, ‘На этой неделе’).",
                    "Представления: Канбан / Список / Календарь / Гант.",
                ],
                icon=_icon("FILTER_ALT"),
            ),
            _section_card(
                "Мобильные клиенты",
                [
                    "Нативные действия и уведомления, офлайн-режим.",
                ],
                icon=_icon("PHONE_IPHONE"),
            ),
        ]
    )


def _tab6(_page: ft.Page) -> ft.Control:
    return _grid(
        [
            _section_card(
                "AI-помощник",
                [
                    "Автозаполнение названий/тегов/исполнителей по аналогам.",
                    "Советы по автоматизации и шаблонные подзадачи.",
                    "Подсказки по узким местам и рискам.",
                ],
                icon=_icon("SMART_TOY_OUTLINED"),
            ),
            _section_card(
                "Low-Code автоматизация",
                [
                    "Конструктор «Если-то»: триггеры → действия (Slack, email, webhooks).",
                ],
                icon=_icon("AUTO_MODE"),
            ),
            _section_card(
                "Маркетплейс",
                [
                    "Плагины и интеграции от сторонних разработчиков.",
                ],
                icon=_icon("EXTENSION")),
        ]
    )


# Сопоставление путей-вкладок
_TABS: list[tuple[str, str, str, callable]] = [
    ("",          "Фундамент",     "HUB_OUTLINED",     _tab1),
    ("it",        "IT-процессы",   "TERMINAL",         _tab2),
    ("business",  "Бизнес",        "BUSINESS_CENTER",  _tab3),
    ("collab",    "Коллаборация",  "GROUPS",           _tab4),
    ("ux",        "UX/UI",         "STYLE",            _tab5),
    ("extras",    "Фишки",         "AUTO_AWESOME",     _tab6),
]
_SLUG_TO_INDEX = {slug: i for i, (slug, *_rest) in enumerate(_TABS)}


def _selected_index_from_route(route: str | None) -> int:
    path = (route or "").split("?")[0].split("#")[0]
    # ожидаем /blueprint или /blueprint/<slug>
    parts = [p for p in (path or "/").split("/") if p]
    slug = parts[1] if len(parts) > 1 and parts[0] == "blueprint" else ""
    return _SLUG_TO_INDEX.get(slug, 0)


# ── view ─────────────────────────────────────────────────────────────────────
def view(page: ft.Page) -> ft.View:
    selected_idx = _selected_index_from_route(page.route or "/blueprint")

    # Сбор табов c контентом
    tab_controls: list[ft.Tab] = []
    for i, (slug, title, icon_name, builder) in enumerate(_TABS):
        content = builder(page)
        tab_controls.append(
            ft.Tab(
                text=title,
                icon=_icon(icon_name),
                content=ft.Container(content, padding=0),
            )
        )

    tabs = ft.Tabs(
        selected_index=selected_idx,
        animation_duration=150,
        tabs=tab_controls,
        expand=False,  # сами карты переносятся, вкладки — в одну строку
    )

    # Синхронизация URL при переключении
    def _on_tabs_change(_e: ft.ControlEvent) -> None:
        idx = int(getattr(tabs, "selected_index", 0) or 0)
        slug = _TABS[idx][0]
        page.go("/blueprint" if not slug else f"/blueprint/{slug}")

    tabs.on_change = _on_tabs_change

    body = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Блюпринт", size=22, weight="w800"),
                    ft.Container(expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=10),
            tabs,
        ],
        spacing=0,
        tight=True,
    )

    return page_scaffold(page, title="Блюпринт", route="/blueprint", body=body)
