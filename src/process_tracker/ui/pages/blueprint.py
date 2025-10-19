# src/process_tracker/ui/pages/blueprint.py
from __future__ import annotations
import flet as ft

from ..components.shell import page_scaffold


def _alpha(c: str, a: float) -> str:
    try:
        return ft.colors.with_opacity(a, c)
    except Exception:
        return c


def _section_card(title: str, bullets: list[str], *, icon=None) -> ft.Container:
    head = ft.Row(
        [ft.Icon(icon or ft.icons.AUTO_AWESOME, size=16), ft.Text(title, size=13, color=ft.colors.ON_SURFACE_VARIANT)],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    items = ft.Column(
        [
            ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=14, opacity=0.9), ft.Text(b, selectable=True)], spacing=8)
            for b in bullets
        ],
        spacing=6,
        tight=True,
    )

    return ft.Container(
        content=ft.Column([head, ft.Container(height=8), items], spacing=0, tight=True),
        padding=14,
        border_radius=14,
        bgcolor=_alpha(ft.colors.SURFACE, 0.06),
        border=ft.border.all(1, _alpha(ft.colors.ON_SURFACE, 0.06)),
    )


def _grid(cards: list[ft.Control]) -> ft.Row:
    # совместимая сетка: перенос по рядам без ResponsiveRow
    tile_w = 440
    return ft.Row(
        [ft.Container(c, width=tile_w) for c in cards],
        spacing=12,
        run_spacing=12,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def view(page: ft.Page) -> ft.View:
    # ----- вкладка 1: Базовый Фундамент -------------------------------------------------
    t1_cards = _grid(
        [
            _section_card(
                "Гибкость и настраиваемость",
                [
                    "Конструктор процессов без кода (формы, статусы, роли).",
                    "Разные типы процессов с собственными полями и правилами.",
                    "Ветвления/параллельные этапы/условия в маршрутах.",
                ],
                icon=ft.icons.BUILD_CIRCLE_OUTLINED,
            ),
            _section_card(
                "Права доступа (RBAC)",
                [
                    "Тонкие разрешения: читать/создавать/редактировать/удалять.",
                    "Группы/роли + маски вроде task.* и admin.*.",
                ],
                icon=ft.icons.ADMIN_PANEL_SETTINGS_OUTLINED,
            ),
            _section_card(
                "API-first и интеграции",
                [
                    "REST API и webhooks для событий.",
                    "Мессенджеры (Slack/Teams), Drive/Confluence/Notion.",
                    "GitHub/GitLab/Jira/мониторинг/CRM/ERP/BI.",
                ],
                icon=ft.icons.SYNC_ALT,
            ),
            _section_card(
                "Производительность и надежность",
                [
                    "Горизонтальное масштабирование, очереди, кэш.",
                    "Минимальные простои, миграции без простоев.",
                ],
                icon=ft.icons.SPEED,
            ),
        ]
    )

    # ----- вкладка 2: IT-процессы --------------------------------------------------------
    t2_cards = _grid(
        [
            _section_card(
                "Глубокая связь с кодом",
                [
                    "Линки на коммиты/ветки/PR прямо из задач.",
                    "Автоматические статусы CI/CD в карточке задачи.",
                ],
                icon=ft.icons.CODE,
            ),
            _section_card(
                "Шаблоны IT-workflow",
                [
                    "Баги/фичи/инциденты/рефакторинг — готовые конфигурации.",
                    "Поля ‘среда’, ‘версия’, ‘компонент’.",
                ],
                icon=ft.icons.INTEGRATION_INSTRUCTIONS,
            ),
            _section_card(
                "Инциденты и SLA",
                [
                    "Приоритизация P0–P2, таймеры реакции/решения.",
                    "Постмортем — шаблон и артефакты расследования.",
                ],
                icon=ft.icons.EMERGENCY,
            ),
        ]
    )

    # ----- вкладка 3: Бизнес-процессы ----------------------------------------------------
    t3_cards = _grid(
        [
            _section_card(
                "Визуальные конструкторы (No-Code)",
                [
                    "Рисуем блок-схему — получаем маршрут и формы.",
                    "Ветвления и условия доступны аналитикам.",
                ],
                icon=ft.icons.SCHEMA,
            ),
            _section_card(
                "Формы и сбор данных",
                [
                    "Валидаторы, справочники, зависимости полей.",
                    "Импорт/экспорт, дубликаты, маски ввода.",
                ],
                icon=ft.icons.DYNAMIC_FORM,
            ),
            _section_card(
                "BI и метрики",
                [
                    "KPI: время цикла, загрузка, bottlenecks.",
                    "Экспорт в Power BI/Tableau, встроенные отчеты.",
                ],
                icon=ft.icons.ANALYTICS,
            ),
        ]
    )

    # ----- вкладка 4: Коллаборация -------------------------------------------------------
    t4_cards = _grid(
        [
            _section_card(
                "Коммуникации",
                [
                    "Комментарии, треды, @упоминания.",
                    "Q&A внутри задачи — не смешивается с логом действий.",
                ],
                icon=ft.icons.MODE_COMMENT_OUTLINED,
            ),
            _section_card(
                "Уведомления и эскалации",
                [
                    "Гибкие правила, чтобы не спамить.",
                    "Эскалации по таймерам/условиям.",
                ],
                icon=ft.icons.NOTIFICATIONS_ACTIVE_OUTLINED,
            ),
            _section_card(
                "Файлы и история",
                [
                    "Вложения с версиями, предпросмотр.",
                    "Полный аудит изменений в карточке.",
                ],
                icon=ft.icons.ATTACH_FILE,
            ),
        ]
    )

    # ----- вкладка 5: UX/UI --------------------------------------------------------------
    t5_cards = _grid(
        [
            _section_card(
                "Интерфейс класса Linear",
                [
                    "Скорость, минимум отвлекающих элементов.",
                    "Горячие клавиши, быстрые действия, командная палитра.",
                ],
                icon=ft.icons.ROCKET_LAUNCH_OUTLINED,
            ),
            _section_card(
                "Поиск и фильтры",
                [
                    "Глобальный поиск, сохранённые вьюхи (‘Мои баги’, ‘На этой неделе’).",
                    "Представления: Канбан / Список / Календарь / Гант.",
                ],
                icon=ft.icons.FILTER_ALT,
            ),
            _section_card(
                "Мобильные клиенты",
                [
                    "Нативные действия и уведомления, офлайн-режим.",
                ],
                icon=ft.icons.PHONE_IPHONE,
            ),
        ]
    )

    # ----- вкладка 6: «Фишки» ------------------------------------------------------------
    t6_cards = _grid(
        [
            _section_card(
                "AI-помощник",
                [
                    "Автозаполнение названий/тегов/исполнителей по аналогам.",
                    "Советы по автоматизации и шаблонные подзадачи.",
                    "Подсказки по узким местам и рискам.",
                ],
                icon=ft.icons.SMART_TOY_OUTLINED,
            ),
            _section_card(
                "Low-Code автоматизация",
                [
                    "Конструктор «Если-то»: триггеры → действия (Slack, email, webhooks).",
                ],
                icon=ft.icons.AUTO_MODE,
            ),
            _section_card(
                "Маркетплейс",
                [
                    "Плагины и интеграции от сторонних разработчиков.",
                ],
                icon=ft.icons.EXTENSION,
            ),
        ]
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=150,
        tabs=[
            ft.Tab(text="Фундамент", icon=ft.icons.HUB_OUTLINED, content=ft.Container(t1_cards, padding=0)),
            ft.Tab(text="IT-процессы", icon=ft.icons.TERMINAL, content=ft.Container(t2_cards, padding=0)),
            ft.Tab(text="Бизнес", icon=ft.icons.BUSINESS_CENTER, content=ft.Container(t3_cards, padding=0)),
            ft.Tab(text="Коллаборация", icon=ft.icons.GROUPS, content=ft.Container(t4_cards, padding=0)),
            ft.Tab(text="UX/UI", icon=ft.icons.STYLE, content=ft.Container(t5_cards, padding=0)),
            ft.Tab(text="Фишки", icon=ft.icons.AUTO_AWESOME, content=ft.Container(t6_cards, padding=0)),
        ],
        expand=False,  # сами карты переносятся, вкладки — в одну строку
    )

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
