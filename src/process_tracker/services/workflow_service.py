from __future__ import annotations

import asyncio
from typing import Iterable, List, Optional, Dict, Any, AsyncIterable, Tuple, Union

from ..core.workflow.engine import WorkflowEngine, WorkflowStore
from ..core.workflow.models import WorkflowDefinition, Step

# Пытаемся взять дефолтный стор (реализация может отличаться по сигнатуре)
try:
    from ..core.workflow.stores.memory import create_default_store  # type: ignore
except Exception:  # pragma: no cover
    create_default_store = None  # type: ignore[assignment]


class WorkflowService:
    """
    Тонкий сервис над движком:
    - отдаёт схемы
    - вычисляет следующие шаги
    - фильтрует переходы по RBAC (роли/права)
    NB: совместим с разными вариантами create_default_store():
        - может вернуть Store
        - может вернуть (Store, Engine)
    """
    def __init__(self, store: Optional[WorkflowStore] = None, engine: Optional[WorkflowEngine] = None) -> None:
        if store is None and create_default_store:
            try:
                # поддерживаем как create_default_store() -> store,
                # так и -> (store, engine)
                maybe = create_default_store()
                if isinstance(maybe, tuple) and len(maybe) >= 1:
                    store = maybe[0]
                    if engine is None and len(maybe) >= 2 and isinstance(maybe[1], WorkflowEngine):
                        engine = maybe[1]
                else:
                    store = maybe  # type: ignore[assignment]
            except Exception:
                store = store  # leave as None

        if store is None:
            # минимальный in-memory стор-пустышка, чтобы не падать
            class _EmptyStore:  # type: ignore
                async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition:
                    raise KeyError(f"workflow '{wf_id}' not found")

                def list_definitions(self) -> Iterable[WorkflowDefinition]:
                    return []

            store = _EmptyStore()  # type: ignore[assignment]

        self.store: WorkflowStore = store
        self.engine: WorkflowEngine = engine or WorkflowEngine(self.store)

    # ---------------- API ----------------

    async def list_definitions(self) -> List[WorkflowDefinition]:
        src = self.store.list_definitions()
        return await _collect_to_list(src)

    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition:
        wf = await self.store.get_definition(wf_id, version)  # type: ignore[arg-type]
        if wf is None:
            # на случай реализаций, возвращающих Optional
            raise KeyError(f"workflow '{wf_id}' not found")
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


# ---------------- helpers ----------------

async def _collect_to_list(src: Union[Iterable[WorkflowDefinition], AsyncIterable[WorkflowDefinition], asyncio.Future, Any]) -> List[WorkflowDefinition]:
    """
    Универсальный сборщик:
      - Iterable[WorkflowDefinition]          -> list(...)
      - AsyncIterable[WorkflowDefinition]     -> [x async for x in ...]
      - coroutine / Future -> ждём и повторяем процедуру
    """
    # 1) корутина/фьючер
    if asyncio.iscoroutine(src) or isinstance(src, asyncio.Future):
        resolved = await src  # type: ignore[func-returns-value]
        return await _collect_to_list(resolved)

    # 2) async-итерируемое
    if hasattr(src, "__aiter__"):
        out: List[WorkflowDefinition] = []
        async for item in src:  # type: ignore[async-iterable]
            out.append(item)
        return out

    # 3) обычный Iterable
    try:
        return list(src)  # type: ignore[arg-type]
    except TypeError:
        # крайний случай: одиночный объект
        return [src]  # type: ignore[list-item]
