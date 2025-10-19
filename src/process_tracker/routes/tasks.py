from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Task
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "open"
    process_id: int | None = None
    type_id: int | None = None
    assignee_id: int | None = None
    # дополнительные удобные поля, которые положим в fields
    priority: str | None = None
    due_at: str | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assignee_id: int | None = None
    process_id: int | None = None
    type_id: int | None = None
    fields: dict


@router.get("", response_model=List[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db), user=CurrentUser):  # type: ignore
    require_perm(user, "task.read")
    rows = (await db.execute(select(Task))).scalars().all()
    return [
        TaskOut(
            id=r.id,
            title=r.title,
            description=r.description,
            status=r.status,
            assignee_id=r.assignee_id,
            process_id=r.process_id,
            type_id=r.type_id,
            fields=r.fields or {},
        )
        for r in rows
    ]


@router.post("", response_model=TaskOut)
async def create_task(body: TaskIn, db: AsyncSession = Depends(get_db), user=CurrentUser):  # type: ignore
    require_perm(user, "task.create")
    fields = {}
    if body.priority is not None:
        fields["priority"] = body.priority
    if body.due_at is not None:
        fields["due_at"] = body.due_at

    obj = Task(
        title=body.title,
        description=body.description,
        status=body.status,
        process_id=body.process_id,
        type_id=body.type_id,
        assignee_id=body.assignee_id,
        fields=fields,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return TaskOut(
        id=obj.id,
        title=obj.title,
        description=obj.description,
        status=obj.status,
        assignee_id=obj.assignee_id,
        process_id=obj.process_id,
        type_id=obj.type_id,
        fields=obj.fields or {},
    )
