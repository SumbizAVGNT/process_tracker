from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, List, Dict, Any

from pydantic import BaseModel, Field, constr


class StepKind(str, Enum):
    START = "start"
    TASK = "task"
    GATEWAY = "gateway"  # условные/параллельные развилки
    END = "end"


class Condition(BaseModel):
    """Условие перехода. Позже добавим jsonlogic/jmespath/expr-eval."""
    expr: constr(min_length=1) = Field(
        ...,
        description="Выражение (jsonlogic/expr). Пока — строка-заглушка.",
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
    id: constr(min_length=1)
    name: constr(min_length=1)
    kind: StepKind = StepKind.TASK
    assignee_roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    id: constr(min_length=1)
    name: constr(min_length=1)
    version: int = 1
    steps: List[Step]
    transitions: List[Transition]
    meta: Dict[str, Any] = Field(default_factory=dict)
