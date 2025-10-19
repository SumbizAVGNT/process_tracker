from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple

from pydantic import BaseModel, Field, ValidationError


class FieldOption(BaseModel):
    value: str
    label: str


class FieldSchema(BaseModel):
    name: str
    title: str
    type: str = Field(default="text")  # text|textarea|select|int|email|password|checkbox|date|datetime
    required: bool = False
    placeholder: Optional[str] = None
    default: Optional[Any] = None

    # для select
    options: Optional[List[FieldOption]] = None

    # простые ограничения
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None


class FormSchema(BaseModel):
    id: str
    title: str
    fields: List[FieldSchema]


class FormsService:
    """
    Лёгкий in-memory реестр форм.
    В бою можно заменить на БД/файлы/конфиг.
    """

    def __init__(self, forms: Optional[Dict[str, FormSchema]] = None) -> None:
        self._forms: Dict[str, FormSchema] = forms or _default_forms()

    # ---- CRUD (упрощённо) ----

    def list_forms(self) -> List[FormSchema]:
        return list(self._forms.values())

    def get_form(self, form_id: str) -> Optional[FormSchema]:
        return self._forms.get(form_id)

    def upsert_form(self, form: FormSchema) -> None:
        self._forms[form.id] = form

    def delete_form(self, form_id: str) -> bool:
        return self._forms.pop(form_id, None) is not None

    # ---- Валидация данных ----

    def validate_data(self, form_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Возвращает (ok, errors). errors: {field: message}
        """
        form = self.get_form(form_id)
        if not form:
            return False, {"_": "Форма не найдена"}

        errors: Dict[str, str] = {}

        for f in form.fields:
            val = data.get(f.name, None)

            # required
            if f.required and (val is None or (isinstance(val, str) and not val.strip())):
                errors[f.name] = "Обязательное поле"
                continue

            if val is None:
                continue  # пустое — дальше не проверяем

            # типы (минимальный набор)
            if f.type in ("text", "textarea", "email", "password", "select"):
                if not isinstance(val, str):
                    errors[f.name] = "Ожидается строка"
                    continue
                if f.min_length is not None and len(val) < f.min_length:
                    errors[f.name] = f"Минимальная длина: {f.min_length}"
                    continue
                if f.max_length is not None and len(val) > f.max_length:
                    errors[f.name] = f"Максимальная длина: {f.max_length}"
                    continue
                if f.type == "select" and f.options:
                    opts = {o.value for o in f.options}
                    if val not in opts:
                        errors[f.name] = "Недопустимое значение"
                        continue

            elif f.type in ("int", "integer"):
                try:
                    iv = int(val)
                except Exception:
                    errors[f.name] = "Ожидается целое число"
                    continue
                if f.min_value is not None and iv < f.min_value:
                    errors[f.name] = f"Минимальное значение: {f.min_value}"
                    continue
                if f.max_value is not None and iv > f.max_value:
                    errors[f.name] = f"Максимальное значение: {f.max_value}"
                    continue

            # Прочие типы можно добавить по мере надобности

        return (len(errors) == 0), errors


# ---- дефолтные формы (демо) ----

def _default_forms() -> Dict[str, FormSchema]:
    """
    Создаём пару демонстрационных форм.
    ВАЖНО: Pydantic v2 → используем ТОЛЬКО именованные аргументы!
    """
    sev_opts = [
        FieldOption(value="sev0", label="SEV0 — критический простой"),
        FieldOption(value="sev1", label="SEV1 — критично"),
        FieldOption(value="sev2", label="SEV2 — заметно"),
        FieldOption(value="sev3", label="SEV3 — минор"),
    ]

    incident_form = FormSchema(
        id="incident.create",
        title="Инцидент",
        fields=[
            FieldSchema(
                name="title",
                title="Заголовок",
                type="text",
                required=True,
                min_length=3,
                max_length=200,
                placeholder="Коротко сформулируйте проблему",
            ),
            FieldSchema(
                name="severity",
                title="Критичность",
                type="select",
                required=True,
                options=sev_opts,
                default="sev2",
            ),
            FieldSchema(
                name="details",
                title="Описание",
                type="textarea",
                required=False,
                max_length=4000,
                placeholder="Что произошло, где воспроизводится, скриншоты и т.п.",
            ),
        ],
    )

    task_form = FormSchema(
        id="task.create",
        title="Задача",
        fields=[
            FieldSchema(
                name="title",
                title="Название",
                type="text",
                required=True,
                min_length=3,
                max_length=200,
            ),
            FieldSchema(
                name="assignee",
                title="Исполнитель (email)",
                type="email",
                required=False,
                max_length=200,
            ),
            FieldSchema(
                name="estimate",
                title="Оценка (часы)",
                type="int",
                required=False,
                min_value=1,
                max_value=999,
            ),
        ],
    )

    return {
        incident_form.id: incident_form,
        task_form.id: task_form,
    }
