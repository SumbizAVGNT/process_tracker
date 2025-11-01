from __future__ import annotations
"""
RBAC-проверка прав с поддержкой подстановок:
- точные права: "task.create"
- подстановки:  "task.*", "admin.*"
- универсальные: "*", "*.*"

Примеры:
  can({"task.*"}, "task.update")      -> True
  can({"*"}, "anything.what.ever")    -> True
  can({"process.read"}, "task.read")  -> False
"""

from typing import Iterable, Set


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def can(granted: Iterable[str], perm: str) -> bool:
    """
    Проверяет право `perm` с поддержкой шаблонов в наборе `granted`.
    """
    p = _norm(perm)
    if not p:
        return False

    g: Set[str] = {_norm(x) for x in granted if x and str(x).strip()}
    if p in g:
        return True

    # универсальные маски
    if "*" in g or "*.*" in g:
        return True

    # "a.b.c" -> проверим "a.b.*" -> "a.*"
    parts = p.split(".")
    for i in range(len(parts), 0, -1):
        pat = ".".join(parts[: i - 1] + ["*"]) if i > 1 else "*"
        if pat in g:
            return True

    # часто "admin.*" трактуют как суперправо
    if "admin.*" in g:
        return True

    return False
