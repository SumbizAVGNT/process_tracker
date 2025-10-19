from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models_meta import TaskType
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/api/v1/task-types", tags=["task-types"])


class TaskTypeIn(BaseModel):
    key: str = Field(..., max_length=64)
    name: str
    default_fields: dict | None = None


class TaskTypeOut(TaskTypeIn):
    id: int


@router.get("", response_model=List[TaskTypeOut])
async def list_task_types(db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "task_type.read")
    rows = (await db.execute(select(TaskType))).scalars().all()
    return [TaskTypeOut(id=r.id, key=r.key, name=r.name, default_fields=r.default_fields) for r in rows]


@router.post("", response_model=TaskTypeOut)
async def create_task_type(body: TaskTypeIn, db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "task_type.create")
    obj = TaskType(key=body.key, name=body.name, default_fields=body.default_fields)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return TaskTypeOut(id=obj.id, key=obj.key, name=obj.name, default_fields=obj.default_fields)
