from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from ..models import WorkflowDefinition, Step, StepKind, Transition, Condition
from ..engine import WorkflowStore, WorkflowEngine


class MemoryWorkflowStore(WorkflowStore):
    """
    Простое in-memory хранилище.
    Версионирование по целому `version`; по умолчанию отдаём max(version).
    """
    def __init__(self, defs: Iterable[WorkflowDefinition] | None = None) -> None:
        self._defs: Dict[str, Dict[int, WorkflowDefinition]] = {}
        if defs:
            for d in defs:
                self.add(d)

    def add(self, wf: WorkflowDefinition) -> None:
        bucket = self._defs.setdefault(wf.id, {})
        bucket[wf.version] = wf

    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition:
        versions = self._defs.get(wf_id) or {}
        if not versions:
            raise KeyError(f"workflow '{wf_id}' not found")
        if version is None:
            version = max(versions.keys())
        try:
            return versions[version]
        except KeyError as e:
            raise KeyError(f"workflow '{wf_id}' version {version} not found") from e

    async def list_definitions(self) -> Iterable[WorkflowDefinition]:
        for _, bucket in self._defs.items():
            # отдаём только максимальные версии
            if bucket:
                yield bucket[max(bucket.keys())]


def _sample_wf() -> WorkflowDefinition:
    """Мини-схема: start -> triage(gateway) -> do_task -> end"""
    steps: List[Step] = [
        Step(id="start", name="Start", kind=StepKind.START),
        Step(id="triage", name="Triage", kind=StepKind.GATEWAY),
        Step(id="do_task", name="Do Task", kind=StepKind.TASK, assignee_roles=["user"], permissions=["task.update"]),
        Step(id="end", name="Done", kind=StepKind.END),
    ]
    transitions: List[Transition] = [
        Transition(name="to_triage", source="start", target="triage"),
        # Пока условие-заглушка True; позже можно заменить на jsonlogic
        Transition(name="approve", source="triage", target="do_task", condition=Condition(expr="true")),
        Transition(name="finish", source="do_task", target="end"),
    ]
    return WorkflowDefinition(
        id="sample.process",
        name="Sample Process",
        version=1,
        steps=steps,
        transitions=transitions,
        meta={"category": "demo"},
    )


def create_default_store(validated: bool = True) -> Tuple[MemoryWorkflowStore, WorkflowEngine]:
    store = MemoryWorkflowStore([_sample_wf()])
    engine = WorkflowEngine(store)
    if validated:
        # провалидируем все схемы
        async def _validate_all():
            async for_def in _aiter(store.list_definitions())
            for wf in for_def:
                await engine.validate(wf)
        # небольшой трюк без внешнего event loop
        import asyncio as _asyncio
        try:
            loop = _asyncio.get_running_loop()
            loop.create_task(_validate_all())
        except RuntimeError:
            _asyncio.run(_validate_all())
    return store, engine


async def _aiter(iterable) -> list:
    # вспом. адаптер: сделать список из async-несовместимого Iterable
    return list(iterable)
