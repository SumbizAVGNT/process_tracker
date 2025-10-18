from __future__ import annotations

from typing import Iterable, List, Optional, Dict, Any

from ..core.workflow.engine import WorkflowEngine, WorkflowStore
from ..core.workflow.models import WorkflowDefinition, Step
from ..core.workflow.stores.memory import create_default_store


class WorkflowService:
    """
    Тонкий сервис над движком:
    - отдаёт схемы
    - вычисляет следующие шаги
    - фильтрует переходы по RBAC (роли/права)
    """
    def __init__(self, store: Optional[WorkflowStore] = None, engine: Optional[WorkflowEngine] = None) -> None:
        if store is None or engine is None:
            s, e = create_default_store()
            store = store or s
            engine = engine or e
        self.store = store
        self.engine = engine

    async def list_definitions(self) -> List[WorkflowDefinition]:
        return list(await _to_list_async(self.store.list_definitions()))

    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition:
        wf = await self.store.get_definition(wf_id, version)
        await self.engine.validate(wf)
        return wf

    async def next_steps(
        self,
        wf_id: str,
        current_step_id: str,
        context: Dict[str, Any],
        *,
        user_roles: Iterable[str] = (),
        user_perms: Iterable[str] = (),
    ) -> List[Step]:
        wf = await self.get_definition(wf_id)
        steps = await self.engine.next_steps(wf, current_step_id, context)
        # RBAC-фильтр
        allowed: List[Step] = []
        for s in steps:
            if await self.engine.can_transition(s, user_roles=user_roles, user_perms=user_perms):
                allowed.append(s)
        return allowed


async def _to_list_async(it) -> list:
    # store.list_definitions() возвращает обычный Iterable,
    # но держим адаптер на случай будущего async-итератора.
    return list(it)
