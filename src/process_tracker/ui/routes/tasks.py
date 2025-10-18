# src/process_tracker/routes/tasks.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.di import session_dependency
from ..db.models import Task
from ..services.task_service import TaskService
from .rate_limit import rate_limit

router = APIRouter()


# ---------- Schemas ----------

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True


class TaskCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskUpdateIn(BaseModel):
    done: bool


# ---------- Endpoints ----------

@router.get("/tasks", response_model=List[TaskOut], dependencies=[Depends(rate_limit)])
async def list_tasks(session: AsyncSession = Depends(session_dependency)):
    svc = TaskService(session)
    items: list[Task] = await svc.list()
    return items


@router.post("/tasks", response_model=TaskOut, status_code=201, dependencies=[Depends(rate_limit)])
async def create_task(data: TaskCreateIn, session: AsyncSession = Depends(session_dependency)):
    svc = TaskService(session)
    item = await svc.create(data.title.strip())
    return item


@router.patch("/tasks/{task_id}", response_model=dict, dependencies=[Depends(rate_limit)])
async def set_done(task_id: int, data: TaskUpdateIn, session: AsyncSession = Depends(session_dependency)):
    svc = TaskService(session)
    changed = await svc.set_done(task_id, data.done)
    if not changed:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.delete("/tasks/{task_id}", response_model=dict, dependencies=[Depends(rate_limit)])
async def delete_task(task_id: int, session: AsyncSession = Depends(session_dependency)):
    svc = TaskService(session)
    removed = await svc.remove(task_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}
