from __future__ import annotations

import re
from typing import Dict, Any, Tuple, List

from .schemas import FormSchema, FieldType


def validate_data(schema: FormSchema, data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Базовая валидация данных формы.
    Возвращает (ok, errors), где errors: {field_id: [errors...]}
    """
    errors: Dict[str, List[str]] = {}

    for f in schema.fields:
        val = data.get(f.id, None)

        # required
        if f.required and (val is None or val == "" or val == []):
            errors.setdefault(f.id, []).append("Обязательное поле")
            continue

        if val is None:
            continue  # нет значения — пропускаем дальнейшие проверки

        # по типам (минимальные проверки)
        if f.type in (FieldType.TEXT, FieldType.TEXTAREA):
            s = str(val)
            if f.min_length is not None and len(s) < f.min_length:
                errors.setdefault(f.id, []).append(f"Минимум {f.min_length} символов")
            if f.max_length is not None and len(s) > f.max_length:
                errors.setdefault(f.id, []).append(f"Максимум {f.max_length} символов")
            if f.pattern and not re.fullmatch(f.pattern, s or ""):
                errors.setdefault(f.id, []).append("Неверный формат")

        elif f.type == FieldType.NUMBER:
            try:
                num = float(val)
            except Exception:
                errors.setdefault(f.id, []).append("Должно быть числом")
                continue
            if f.min_value is not None and num < f.min_value:
                errors.setdefault(f.id, []).append(f"Минимум {f.min_value}")
            if f.max_value is not None and num > f.max_value:
                errors.setdefault(f.id, []).append(f"Максимум {f.max_value}")

        elif f.type in (FieldType.SELECT, FieldType.MULTISELECT):
            opts = {o.value for o in f.options}
            if f.type == FieldType.SELECT:
                if str(val) not in opts:
                    errors.setdefault(f.id, []).append("Недопустимое значение")
            else:
                arr = [str(x) for x in (val or [])]
                unknown = [x for x in arr if x not in opts]
                if unknown:
                    errors.setdefault(f.id, []).append(f"Неизвестные значения: {', '.join(unknown)}")

        # DATE / CHECKBOX / FILE / USER — пока без специальных правил (добавим позже)

    return (len(errors) == 0), errors
