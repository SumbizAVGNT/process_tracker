from __future__ import annotations

import asyncio
from typing import Any, Set


class Broadcaster:
    """
    Простейший in-memory pub/sub:
      - subscribe() -> asyncio.Queue: подписка на события
      - publish(event: dict) -> None: разослать событие всем подписчикам
      - unsubscribe(queue) -> None: отписка
    Потокобезопасно для asyncio-задач внутри одного процесса.
    """

    def __init__(self) -> None:
        self._subs: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subs.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            self._subs.discard(q)

    async def publish(self, event: dict[str, Any]) -> None:
        # рассылаем неблокирующе всем текущим подписчикам
        async with self._lock:
            targets = list(self._subs)
        for q in targets:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # если когда-то сделаем ограниченную очередь — не роняемся
                pass


# Глобальный экземпляр
events = Broadcaster()
