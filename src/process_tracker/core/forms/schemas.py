from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    USER = "user"
    FILE = "file"


class FieldOption(BaseModel):
    value: str
    label: str


class FieldSchema(BaseModel):
    id: str
    label: str
    type: FieldType
    required: bool = False
    description: Optional[str] = None

    # Валидаторы по типу:
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # regex

    # Для select:
    options: List[FieldOption] = Field(default_factory=list)

    # Доп. метаданные для UI:
    ui: Dict[str, Any] = Field(default_factory=dict)


class FormSchema(BaseModel):
    id: str
    name: str
    version: int = 1
    fields: List[FieldSchema]
    meta: Dict[str, Any] = Field(default_factory=dict)
