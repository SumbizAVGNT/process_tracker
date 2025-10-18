from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, List, Dict, Any

from pydantic import BaseModel, Field


class StepKind(str, Enum):
    START = "start"
    TASK = "task"
    GATEWAY = "gateway"  # условные/параллельные развилки
    END = "end"


class Condition(BaseModel):
    """Условие перехода. Поддержим jsonlogic или JMESPath позднее."""
    expr: str = Field(
        ...,
        description="Выражение (jsonlogic или другая DSL). Пока — строка-заглушка.",
    )
    kind: Literal["jsonlogic", "expr"] = "jsonlogic"


class Transition(BaseModel):
    """Переход из шага в шаг с условием."""
    name: Optional[str] = None
    source: str = Field(..., description="ID шага-источника")
    target: str = Field(..., description="ID шага-назначения")
    condition: Optional[Condition] = None
    is_parallel_fork: bool = False
    is_parallel_join: bool = False


class Step(BaseModel):
    id: str
    name: str
    kind: StepKind = StepKind.TASK
    assignee_roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    version: int = 1
    steps: List[Step]
    transitions: List[Transition]
    meta: Dict[str, Any] = Field(default_factory=dict)
