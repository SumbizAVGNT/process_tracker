from __future__ import annotations

from typing import Any, Dict, List

from ..workflow import (
    WorkflowDefinition as EngineWorkflow,
    Step,
    Transition,
    StepKind,
    Condition,
)

from .definitions import BlueprintDefinition


def _node_to_step(node: Dict[str, Any]) -> Step:
    """
    Ожидаемые (но не обязательные) поля node:
      id: str
      name/title: str
      type: "start" | "task" | "gateway" | "end"
      roles: list[str]
      perms/permissions: list[str]
      meta: dict
    """
    node_id = str(node.get("id") or node.get("key") or "")
    if not node_id:
        raise ValueError("Blueprint node is missing required 'id' (or 'key')")

    name = str(node.get("name") or node.get("title") or node_id)

    # вид шага
    t = (node.get("type") or node.get("kind") or "task").strip().lower()
    kind = {
        "start": StepKind.START,
        "task": StepKind.TASK,
        "gateway": StepKind.GATEWAY,
        "end": StepKind.END,
    }.get(t, StepKind.TASK)

    assignee_roles = list(node.get("roles") or node.get("assignee_roles") or [])
    permissions = list(node.get("perms") or node.get("permissions") or [])
    meta = dict(node.get("meta") or {})

    return Step(
        id=node_id,
        name=name,
        kind=kind,
        assignee_roles=assignee_roles,
        permissions=permissions,
        meta=meta,
    )


def _edge_to_transition(edge: Dict[str, Any]) -> Transition:
    """
    Ожидаемые поля edge:
      source/from, target/to
      name (опц.)
      condition: str | {expr, kind}
      parallel: "fork" | "join" | bool флаги
    """
    source = str(edge.get("source") or edge.get("from") or "")
    target = str(edge.get("target") or edge.get("to") or "")
    if not source or not target:
        raise ValueError("Blueprint edge requires 'source'/'target' (or 'from'/'to')")

    name = edge.get("name")
    cond = edge.get("condition")
    if isinstance(cond, str) and cond.strip():
        condition = Condition(expr=cond.strip(), kind="jsonlogic")
    elif isinstance(cond, dict) and cond.get("expr"):
        condition = Condition(expr=str(cond["expr"]), kind=str(cond.get("kind") or "jsonlogic"))
    else:
        condition = None

    par = (edge.get("parallel") or "").strip().lower() if isinstance(edge.get("parallel"), str) else None
    is_fork = bool(edge.get("is_parallel_fork")) or (par == "fork")
    is_join = bool(edge.get("is_parallel_join")) or (par == "join")

    return Transition(
        name=name,
        source=source,
        target=target,
        condition=condition,
        is_parallel_fork=is_fork,
        is_parallel_join=is_join,
    )


def compile_to_workflow(bp: BlueprintDefinition) -> EngineWorkflow:
    """
    Конвертируем блюпринт редактора (nodes/edges) в боевую схему движка.
    Далее можно валидировать через WorkflowEngine.validate().
    """
    steps: List[Step] = [_node_to_step(n) for n in bp.nodes]
    transitions: List[Transition] = [_edge_to_transition(e) for e in bp.edges]

    meta = {
        "source": "blueprint",
        "blueprint_key": bp.key,
        "blueprint_version": bp.version,
    }

    return EngineWorkflow(
        id=bp.key,
        name=bp.title,
        version=bp.version,
        steps=steps,
        transitions=transitions,
        meta=meta,
    )
