from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class BlueprintDefinition:
    """
    Черновик/блюпринт workflow для редактора (no-code):
    - key: уникальный ключ (например, "it.incident")
    - title: человекочитаемое имя
    - nodes/edges: произвольные структуры редактора графа
    - version: инкрементальная версия
    - created_at/updated_at: метки времени (UTC)
    """
    key: str
    title: str
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
