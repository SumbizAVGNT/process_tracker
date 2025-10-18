from __future__ import annotations

from typing import Dict, List, Tuple, Any

from ..core.forms.schemas import FormSchema, FieldSchema, FieldType, FieldOption
from ..core.forms.validators import validate_data


class FormsService:
    """
    Простой in-memory реестр схем форм.
    Позже можно подменить на DAL (БД/kv-store), сигнатуры методов сохраняем.
    """

    def __init__(self, forms: Dict[str, FormSchema] | None = None) -> None:
        self._forms: Dict[str, FormSchema] = forms or _default_forms()

    async def list_forms(self) -> List[FormSchema]:
        return list(self._forms.values())

    async def get_form(self, form_id: str) -> FormSchema:
        try:
            return self._forms[form_id]
        except KeyError as e:
            raise KeyError(f"form '{form_id}' not found") from e

    async def validate(self, form_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        schema = await self.get_form(form_id)
        return validate_data(schema, data)


def _default_forms() -> Dict[str, FormSchema]:
    """
    Набор демонстрационных форм:
      - task.create: создание задачи
      - incident.report: описание инцидента
    """
    task_create = FormSchema(
        id="task.create",
        name="Создание задачи",
        version=1,
        fields=[
            FieldSchema(
                id="title",
                label="Заголовок",
                type=FieldType.TEXT,
                required=True,
                min_length=3,
                max_length=120,
                ui={"placeholder": "Коротко опишите задачу"},
            ),
            FieldSchema(
                id="description",
                label="Описание",
                type=FieldType.TEXTAREA,
                required=False,
                max_length=4000,
                ui={"min_lines": 3, "max_lines": 8},
            ),
            FieldSchema(
                id="priority",
                label="Приоритет",
                type=FieldType.SELECT,
                required=True,
                options=[
                    FieldOption(value="P1", label="P1 — критично"),
                    FieldOption(value="P2", label="P2 — высоко"),
                    FieldOption(value="P3", label="P3 — средне"),
                    FieldOption(value="P4", label="P4 — низко"),
                ],
                ui={"dense": True},
            ),
            FieldSchema(
                id="due_date",
                label="Дедлайн",
                type=FieldType.DATE,
                required=False,
            ),
            FieldSchema(
                id="assignee",
                label="Исполнитель",
                type=FieldType.USER,
                required=False,
                ui={"hint": "Оставьте пустым — назначим позже"},
            ),
        ],
        meta={"category": "tasks"},
    )

    incident_report = FormSchema(
        id="incident.report",
        name="Отчёт об инциденте",
        version=1,
        fields=[
            FieldSchema(
                id="summary",
                label="Краткое описание",
                type=FieldType.TEXT,
                required=True,
                min_length=5,
                max_length=200,
            ),
            FieldSchema(
                id="impact",
                label="Влияние",
                type=FieldType.SELECT,
                required=True,
                options=[
                    FieldOption("sev0", "SEV0 — критический простой"),
                    FieldOption("sev1", "SEV1 — значимый сбой"),
                    FieldOption("sev2", "SEV2 — частичное ухудшение"),
                ],
            ),
            FieldSchema(
                id="systems",
                label="Затронутые системы",
                type=FieldType.MULTISELECT,
                required=False,
                options=[
                    FieldOption("api", "Public API"),
                    FieldOption("auth", "Auth Service"),
                    FieldOption("db", "Database"),
                    FieldOption("ui", "Frontend UI"),
                ],
            ),
        ],
        meta={"category": "incidents"},
    )

    return {task_create.id: task_create, incident_report.id: incident_report}
