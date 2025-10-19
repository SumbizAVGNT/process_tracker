from __future__ import annotations

from typing import AsyncIterator, Dict, Iterable, Optional, List, Any

from .definitions import BlueprintDefinition, utcnow


class MemoryBlueprintStore:
    """
    Простой in-memory стор для блюпринтов workflow.
    Совместим с async-роутами/сервисами.
    """
    def __init__(self) -> None:
        self._defs: Dict[str, BlueprintDefinition] = {}

    # -------- CRUD --------

    async def list_definitions(self) -> AsyncIterator[BlueprintDefinition]:
        """Асинхронный итератор: `async for bp in store.list_definitions(): ...`"""
        for d in self._defs.values():
            yield d

    async def list_as_list(self) -> list[BlueprintDefinition]:
        """Удобный списковый вариант, если нужен сразу весь список."""
        return list(self._defs.values())

    async def get_definition(self, key: str) -> Optional[BlueprintDefinition]:
        return self._defs.get(key)

    async def upsert_definition(
        self,
        key: str,
        *,
        title: Optional[str] = None,
        nodes: Optional[Iterable[dict]] = None,
        edges: Optional[Iterable[dict]] = None,
        version: Optional[int] = None,
        bump_if_changed: bool = True,
    ) -> BlueprintDefinition:
        """
        Создаёт или обновляет блюпринт.
        Если version не указан и содержимое заметно изменилось — инкрементим версию (bump_if_changed=True).
        """
        existing = self._defs.get(key)
        if existing is None:
            obj = BlueprintDefinition(
                key=key,
                title=title or key,
                nodes=list(nodes or []),
                edges=list(edges or []),
                version=int(version or 1),
            )
            self._defs[key] = obj
            return obj

        # --- update ---
        changed = False

        if title is not None and title != existing.title:
            existing.title = title
            changed = True

        if nodes is not None:
            new_nodes = list(nodes)
            if new_nodes != existing.nodes:
                existing.nodes = new_nodes
                changed = True

        if edges is not None:
            new_edges = list(edges)
            if new_edges != existing.edges:
                existing.edges = new_edges
                changed = True

        if version is not None:
            new_version = int(version)
            if new_version != existing.version:
                existing.version = new_version
        elif changed and bump_if_changed:
            existing.version += 1

        existing.updated_at = utcnow()
        return existing

    async def delete_definition(self, key: str) -> bool:
        return self._defs.pop(key, None) is not None

    # -------- Утилиты --------

    async def to_dict(self, key: str) -> Optional[dict]:
        obj = await self.get_definition(key)
        return obj.to_dict() if obj else None


# Фабрика стора по умолчанию — именно её импортирует сервис/роутер
def create_default_store() -> MemoryBlueprintStore:
    return MemoryBlueprintStore()
