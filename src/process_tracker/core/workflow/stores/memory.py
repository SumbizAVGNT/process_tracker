from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Iterable


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WorkflowDefinition:
    """
    Минимальная модель определения workflow:
    - key: уникальный ключ (например, "it.incident")
    - title: человекочитаемое имя
    - nodes/edges: произвольные структуры вашего редактора графа
    - version: инкрементальная версия
    - created_at/updated_at: метки времени
    """
    key: str
    title: str
    nodes: List[dict] = field(default_factory=list)
    edges: List[dict] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


class MemoryWorkflowStore:
    """
    Простой in-memory стор для определений workflow.
    Совместим как с синхронной, так и с async-логикой роутов/сервисов.
    """
    def __init__(self) -> None:
        self._defs: Dict[str, WorkflowDefinition] = {}

    # -------- CRUD по определениям --------

    async def list_definitions(self) -> AsyncGenerator[WorkflowDefinition, None]:
        """
        Асинхронный генератор — чтобы было удобно делать `async for` без лишних обёрток.
        """
        for d in self._defs.values():
            yield d

    async def get_definition(self, key: str) -> Optional[WorkflowDefinition]:
        return self._defs.get(key)

    async def upsert_definition(
        self,
        key: str,
        *,
        title: Optional[str] = None,
        nodes: Optional[Iterable[dict]] = None,
        edges: Optional[Iterable[dict]] = None,
        version: Optional[int] = None,
    ) -> WorkflowDefinition:
        existing = self._defs.get(key)
        if existing is None:
            obj = WorkflowDefinition(
                key=key,
                title=title or key,
                nodes=list(nodes or []),
                edges=list(edges or []),
                version=version or 1,
            )
            self._defs[key] = obj
            return obj

        # update
        if title is not None:
            existing.title = title
        if nodes is not None:
            existing.nodes = list(nodes)
        if edges is not None:
            existing.edges = list(edges)
        if version is not None:
            existing.version = int(version)
        existing.updated_at = utcnow()
        return existing

    async def delete_definition(self, key: str) -> bool:
        return self._defs.pop(key, None) is not None

    # -------- Утилиты (опционально) --------

    async def to_dict(self, key: str) -> Optional[dict]:
        obj = await self.get_definition(key)
        return asdict(obj) if obj else None


# Фабрика стора по умолчанию — именно её импортирует сервис
def create_default_store() -> MemoryWorkflowStore:
    return MemoryWorkflowStore()
