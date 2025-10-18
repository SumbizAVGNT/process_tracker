from __future__ import annotations

from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, Field

from process_tracker.core.workflow.models import Condition


class Trigger(BaseModel):
    """Триггер правила: событие/расписание/webhook."""
    type: Literal["event", "schedule", "webhook"]
    match: Dict[str, Any] = Field(default_factory=dict)  # например: {"event": "task.created"}


class Action(BaseModel):
    """Действие: http/webhook/создание задачи/смена статуса/уведомление и т.д."""
    type: Literal["http", "webhook", "create_task", "change_status", "notify"]
    params: Dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    trigger: Trigger
    conditions: List[Condition] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
