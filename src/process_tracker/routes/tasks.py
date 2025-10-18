from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..services.task_service import TaskService  # через сервис публикуем события

router = APIRouter(tags=["tasks"])

class TaskIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок задачи")

class TaskSetDoneIn(BaseModel):
    done: bool = Field(..., description="Статус выполнения")

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

def _svc(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session)

@router.get("/tasks", response_model=List[TaskOut])
async def list_tasks(svc: TaskService = Depends(_svc)):
    items = await svc.list()
    return [TaskOut.model_validate({
        "id": t.id, "title": t.title, "done": bool(getattr(t, "done", False)),
        "created_at": getattr(t, "created_at", None),
        "updated_at": getattr(t, "updated_at", None),
    }) for t in items]

@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskIn, svc: TaskService = Depends(_svc)):
    item = await svc.create(title=body.title.strip())
    return TaskOut(id=item.id, title=item.title, done=getattr(item, "done", False),
                   created_at=getattr(item, "created_at", None),
                   updated_at=getattr(item, "updated_at", None))

@router.patch("/tasks/{task_id}/done", response_model=TaskOut)
async def set_done(task_id: int, body: TaskSetDoneIn, svc: TaskService = Depends(_svc)):
    changed = await svc.set_done(task_id, body.done)
    if not changed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    # обновим список и вернём актуальный объект
    items = await svc.list()
    item = next((x for x in items if getattr(x, "id", None) == task_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return TaskOut(id=item.id, title=item.title, done=getattr(item, "done", False),
                   created_at=getattr(item, "created_at", None),
                   updated_at=getattr(item, "updated_at", None))

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, svc: TaskService = Depends(_svc)):
    deleted = await svc.remove(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return
