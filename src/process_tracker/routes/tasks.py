from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Task  # ваш текущий класс
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    process_id: int | None = None
    type_key: str | None = None
    title: str
    priority: str | None = None
    assignee_email: str | None = None
    due_at: str | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    status: str | None = None
    priority: str | None = None
    assignee_email: str | None = None
    process_id: int | None = None


@router.get("", response_model=List[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "task.read")
    rows = (await db.execute(select(Task))).scalars().all()
    return [
        TaskOut(
            id=r.id,
            title=getattr(r, "title", f"Task #{r.id}"),
            status=getattr(r, "status", None),
            priority=getattr(r, "priority", None),
            assignee_email=getattr(r, "assignee_email", None),
            process_id=getattr(r, "process_id", None),
        )
        for r in rows
    ]


@router.post("", response_model=TaskOut)
async def create_task(body: TaskIn, db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "task.create")
    obj = Task(
        title=body.title,
        status=getattr(Task, "status", None) and "open" or None,
        priority=body.priority,
        assignee_email=body.assignee_email,
        process_id=body.process_id,
    )
    db.add(obj); await db.commit(); await db.refresh(obj)
    return TaskOut(
        id=obj.id,
        title=getattr(obj, "title", f"Task #{obj.id}"),
        status=getattr(obj, "status", None),
        priority=getattr(obj, "priority", None),
        assignee_email=getattr(obj, "assignee_email", None),
        process_id=getattr(obj, "process_id", None),
    )
