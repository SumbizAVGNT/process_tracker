from __future__ import annotations

import asyncio
from typing import Protocol, Optional, Iterable, Dict, Any, List, Set

from .models import WorkflowDefinition, Step, Transition, Condition


class WorkflowStore(Protocol):
    """Интерфейс хранилища схем (для БД/кэша/файлов)."""
    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition: ...
    async def list_definitions(self) -> Iterable[WorkflowDefinition]: ...


class WorkflowEngine:
    """
    Мини-движок маршрутов.
    - validate(): базовые инварианты (есть start/end, граф связен и т.д.)
    - next_steps(): отдать потенциальные target-шаги, прошедшие условия
    - can_transition(): проверка RBAC (по ролям/правам) на конкретный шаг
    """

    def __init__(self, store: WorkflowStore):
        self.store = store

    # --------- VALIDATION ---------

    async def validate(self, wf: WorkflowDefinition) -> None:
        ids = {s.id for s in wf.steps}
        if not any(s.kind == s.kind.START for s in wf.steps):
            raise ValueError("Workflow must have START step")
        if not any(s.kind == s.kind.END for s in wf.steps):
            raise ValueError("Workflow must have END step")

        for t in wf.transitions:
            if t.source not in ids or t.target not in ids:
                raise ValueError(f"Transition references unknown step: {t.source} -> {t.target}")

        # TODO: проверка на циклы (опционально)
        # TODO: валидация параллельных веток (fork/join согласованность)

    # --------- EVALUATION ---------

    async def next_steps(
        self,
        wf: WorkflowDefinition,
        current_step_id: str,
        context: Dict[str, Any],
    ) -> List[Step]:
        """Вернуть следующий(ие) шаг(и) по переходам, чьи условия истинны."""
        targets: List[Step] = []
        steps_by_id = {s.id: s for s in wf.steps}
        for tr in self._outgoing(wf, current_step_id):
            if await self._condition_ok(tr.condition, context):
                step = steps_by_id[tr.target]
                targets.append(step)
        return targets

    async def can_transition(
        self,
        step: Step,
        *,
        user_roles: Iterable[str] = (),
        user_perms: Iterable[str] = (),
    ) -> bool:
        """Простая проверка RBAC: роль или право совпадает."""
        roles = {r.lower() for r in user_roles}
        perms = {p.lower() for p in user_perms}
        if not step.assignee_roles and not step.permissions:
            return True
        if roles.intersection({r.lower() for r in step.assignee_roles}):
            return True
        if self._perm_match_any(step.permissions, perms):
            return True
        return False

    # --------- helpers ---------

    def _outgoing(self, wf: WorkflowDefinition, source_id: str) -> Iterable[Transition]:
        return (t for t in wf.transitions if t.source == source_id)

    def _perm_match_any(self, required: Iterable[str], granted: Set[str]) -> bool:
        for perm in required:
            p = (perm or "").strip().lower()
            if not p:
                continue
            if p in granted:
                return True
            parts = p.split(".")
            for i in range(len(parts), 0, -1):
                star = ".".join(parts[: i - 1] + ["*"])
                if star in granted:
                    return True
            if "*.*" in granted or "*" in granted or "admin.*" in granted:
                return True
        return False

    async def _condition_ok(self, cond: Optional[Condition], ctx: Dict[str, Any]) -> bool:
        if cond is None:
            return True
        # TODO: подключить jsonlogic/jmespath/expr-eval. Пока — заглушка True.
        await asyncio.sleep(0)  # отдать цикл, чтобы не блокировать UI
        return True
