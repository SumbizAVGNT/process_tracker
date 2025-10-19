from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import Protocol, Optional, Iterable, Dict, Any, List, Set, Tuple

from .models import WorkflowDefinition, Step, Transition, Condition, StepKind


class WorkflowStore(Protocol):
    """Интерфейс хранилища схем (для БД/кэша/файлов)."""
    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition: ...
    async def list_definitions(self) -> Iterable[WorkflowDefinition]: ...


class InMemoryWorkflowStore:
    """Простой in-memory стор для dev/тестов."""
    def __init__(self, defs: Iterable[WorkflowDefinition] | None = None) -> None:
        self._data: Dict[Tuple[str, int], WorkflowDefinition] = {}
        if defs:
            for d in defs:
                self.add(d)

    def add(self, d: WorkflowDefinition) -> None:
        self._data[(d.id, d.version)] = d

    async def get_definition(self, wf_id: str, version: Optional[int] = None) -> WorkflowDefinition:
        if version is not None:
            key = (wf_id, version)
            if key in self._data:
                return self._data[key]
            raise KeyError(f"Workflow {wf_id}@{version} not found")
        # latest by version
        options = [(v, d) for (i, v), d in self._data.items() if i == wf_id]
        if not options:
            raise KeyError(f"Workflow {wf_id} not found")
        _, latest = max(options, key=lambda p: p[0])
        return latest

    async def list_definitions(self) -> Iterable[WorkflowDefinition]:
        # возвращаем последнюю версию для каждого wf_id
        last: Dict[str, WorkflowDefinition] = {}
        for (wf_id, _), d in self._data.items():
            prev = last.get(wf_id)
            if prev is None or d.version > prev.version:
                last[wf_id] = d
        return list(last.values())


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
        if len(ids) != len(wf.steps):
            raise ValueError("Step IDs must be unique")

        starts = [s for s in wf.steps if s.kind == StepKind.START]
        ends = [s for s in wf.steps if s.kind == StepKind.END]
        if len(starts) != 1:
            raise ValueError("Workflow must have exactly one START step")
        if len(ends) < 1:
            raise ValueError("Workflow must have at least one END step")

        # переходы на существующие узлы
        for t in wf.transitions:
            if t.source not in ids or t.target not in ids:
                raise ValueError(f"Transition references unknown step: {t.source} -> {t.target}")

        # старт не имеет входящих, end не имеет исходящих
        incoming, outgoing = self._build_graph(wf)
        start_id = starts[0].id
        if incoming[start_id]:
            raise ValueError("START step must not have incoming transitions")
        for end in ends:
            if outgoing[end.id]:
                raise ValueError(f"END step '{end.id}' must not have outgoing transitions")

        # связность: все узлы достижимы из START
        reachable = self._reachable_from(start_id, outgoing)
        if reachable != ids:
            missing = ", ".join(sorted(ids - reachable))
            raise ValueError(f"Unreachable steps from START: {missing}")

        # отсутствие циклов (DAG)
        if self._has_cycle(ids, outgoing, incoming):
            raise ValueError("Workflow graph contains a cycle")

        # Базовая согласованность параллельных флагов (не строго)
        for t in wf.transitions:
            if t.is_parallel_fork or t.is_parallel_join:
                # допускаем только на GATEWAY шагах
                if t.is_parallel_fork and wf_step_kind(wf, t.source) != StepKind.GATEWAY:
                    raise ValueError(f"Parallel fork transition must originate from a GATEWAY: {t.source}")
                if t.is_parallel_join and wf_step_kind(wf, t.target) != StepKind.GATEWAY:
                    raise ValueError(f"Parallel join transition must target a GATEWAY: {t.target}")

    # --------- EVALUATION ---------

    async def next_steps(
        self,
        wf: WorkflowDefinition,
        current_step_id: str,
        context: Dict[str, Any],
    ) -> List[Step]:
        """Вернуть следующий(ие) шаг(и) по переходам, чьи условия истинны."""
        steps_by_id = {s.id: s for s in wf.steps}
        targets: List[Step] = []
        for tr in self._outgoing(wf, current_step_id):
            if await self._condition_ok(tr.condition, context):
                targets.append(steps_by_id[tr.target])
        return targets

    async def can_transition(
        self,
        step: Step,
        *,
        user_roles: Iterable[str] = (),
        user_perms: Iterable[str] = (),
    ) -> bool:
        """Простая проверка RBAC: роль или право совпадает, поддержка wildcard."""
        roles = {r.strip().lower() for r in user_roles if r}
        perms = {p.strip().lower() for p in user_perms if p}
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
        """Сопоставление прав с поддержкой '*' и 'admin.*'."""
        granted = {g.strip().lower() for g in granted if g}
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
        """Заглушка для условий: True. (позже — jsonlogic/jmespath)."""
        if cond is None:
            return True
        await asyncio.sleep(0)  # уступить цикл UI/серверу
        return True

    # ---- graph utils ----

    def _build_graph(self, wf: WorkflowDefinition) -> tuple[Dict[str, set[str]], Dict[str, set[str]]]:
        incoming: Dict[str, set[str]] = defaultdict(set)
        outgoing: Dict[str, set[str]] = defaultdict(set)
        ids = {s.id for s in wf.steps}
        for s in ids:
            incoming[s]  # ensure key
            outgoing[s]
        for t in wf.transitions:
            outgoing[t.source].add(t.target)
            incoming[t.target].add(t.source)
        return incoming, outgoing

    def _reachable_from(self, start: str, outgoing: Dict[str, set[str]]) -> set[str]:
        seen: set[str] = set()
        q: deque[str] = deque([start])
        while q:
            v = q.popleft()
            if v in seen:
                continue
            seen.add(v)
            for w in outgoing.get(v, ()):
                if w not in seen:
                    q.append(w)
        return seen

    def _has_cycle(self, ids: set[str], outgoing: Dict[str, set[str]], incoming: Dict[str, set[str]]) -> bool:
        # Kahn’s algorithm for DAG check
        indeg = {v: len(incoming.get(v, ())) for v in ids}
        q = deque([v for v in ids if indeg[v] == 0])
        visited = 0
        while q:
            v = q.popleft()
            visited += 1
            for w in outgoing.get(v, ()):
                indeg[w] -= 1
                if indeg[w] == 0:
                    q.append(w)
        return visited != len(ids)


def wf_step_kind(wf: WorkflowDefinition, step_id: str) -> StepKind:
    for s in wf.steps:
        if s.id == step_id:
            return s.kind
    raise KeyError(f"Unknown step id: {step_id}")
