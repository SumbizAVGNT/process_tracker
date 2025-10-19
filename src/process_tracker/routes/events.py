from __future__ import annotations
import asyncio
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["events"])

# Попытка взять реальный bus; иначе — локальная очередь
try:
    from ..events.bus import bus  # type: ignore
except Exception:
    class _DummyBus:
        def __init__(self) -> None:
            self._subs: list[asyncio.Queue] = []
        async def subscribe(self) -> asyncio.Queue:
            q: asyncio.Queue = asyncio.Queue()
            self._subs.append(q)
            return q
        async def publish(self, event: str, payload: dict) -> None:
            for q in self._subs:
                await q.put({"event": event, "data": payload})
        async def unsubscribe(self, q: asyncio.Queue) -> None:
            if q in self._subs:
                self._subs.remove(q)
    bus = _DummyBus()  # type: ignore

async def _event_stream(topic: Optional[str]) -> AsyncGenerator[bytes, None]:
    # подписка
    try:
        q: asyncio.Queue = await bus.subscribe()  # type: ignore[attr-defined]
    except Exception:
        q = asyncio.Queue()
    try:
        # heartbeat
        yield b":ok\n\n"
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=15.0)
                if isinstance(msg, dict):
                    ev = str(msg.get("event", "message"))
                    if topic and not ev.startswith(topic):
                        continue
                    data = msg.get("data", {})
                    line = f"event: {ev}\ndata: {data}\n\n".encode("utf-8")
                    yield line
                else:
                    yield b":noop\n\n"
            except asyncio.TimeoutError:
                yield b":heartbeat\n\n"
    finally:
        try:
            await bus.unsubscribe(q)  # type: ignore[attr-defined]
        except Exception:
            pass

@router.get("/events/stream")
async def sse_stream(topic: Optional[str] = Query(None)):
    return StreamingResponse(_event_stream(topic), media_type="text/event-stream")
