from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..db.session import get_session
from ..db.dal.task_repo import TaskRepo
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["tasks"])

# ---------- Schemas ----------

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

    @classmethod
    def from_orm_obj(cls, t) -> "TaskOut":
        return cls(
            id=getattr(t, "id"),
            title=getattr(t, "title"),
            done=bool(getattr(t, "done", False)),
            created_at=getattr(t, "created_at", None),
            updated_at=getattr(t, "updated_at", None),
        )

# ---------- Endpoints ----------

@router.get("/tasks", response_model=List[TaskOut])
async def list_tasks(session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    items = await repo.list()
    return [TaskOut.from_orm_obj(x) for x in items]

@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskIn, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    item = await repo.create(title=body.title.strip())
    return TaskOut.from_orm_obj(item)

@router.patch("/tasks/{task_id}/done", response_model=TaskOut)
async def set_done(task_id: int, body: TaskSetDoneIn, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    affected_id = await repo.set_done(task_id, body.done)
    if not affected_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    # перезагрузим объект для ответа
    items = await repo.list()
    found = next((t for t in items if getattr(t, "id", None) == task_id), None)
    if not found:
        # крайне маловероятно, но на всякий
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return TaskOut.from_orm_obj(found)

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    repo = TaskRepo(session)
    deleted_id = await repo.remove(task_id)
    if not deleted_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return
