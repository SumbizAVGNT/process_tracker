from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.dal import TaskRepo

router = APIRouter()

class TaskIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool

@router.get("/tasks", response_model=List[TaskOut])
async def list_tasks(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = TaskRepo(session)
    items = await repo.list()
    items = items[offset : offset + limit]
    return [TaskOut(id=i.id, title=i.title, done=i.done) for i in items]

@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskIn, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    obj = await repo.create(body.title)
    await session.commit()
    return TaskOut(id=obj.id, title=obj.title, done=obj.done)

class TaskDoneIn(BaseModel):
    done: bool = True

@router.patch("/tasks/{task_id}/done", response_model=TaskOut)
async def set_task_done(task_id: int, body: TaskDoneIn, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    updated_id = await repo.set_done(task_id, body.done)
    if not updated_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    await session.commit()
    # простое повторное чтение из списка (можно сделать get_by_id)
    items = await repo.list()
    obj = next((x for x in items if x.id == task_id), None)
    return TaskOut(id=obj.id, title=obj.title, done=obj.done)

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    deleted_id = await repo.remove(task_id)
    if not deleted_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    await session.commit()
    return
