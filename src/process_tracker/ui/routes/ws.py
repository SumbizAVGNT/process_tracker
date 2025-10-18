# src/process_tracker/routes/ws.py

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.events import events

router = APIRouter()


@router.websocket("/ws/tasks")
async def ws_tasks(ws: WebSocket):
    await ws.accept()
    q = await events.subscribe()
    try:
        while True:
            ev = await q.get()
            # Отправляем только события задач
            if isinstance(ev, dict) and str(ev.get("type", "")).startswith("task_"):
                await ws.send_json(ev)
    except WebSocketDisconnect:
        pass
    finally:
        await events.unsubscribe(q)
