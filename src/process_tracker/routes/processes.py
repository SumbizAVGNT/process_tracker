from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Process  # ваш текущий класс
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/api/v1/processes", tags=["processes"])


class ProcessIn(BaseModel):
    type_key: str
    title: str
    assignee_email: str | None = None


class ProcessOut(BaseModel):
    id: int
    title: str
    status: str | None = None
    assignee_email: str | None = None


@router.get("", response_model=List[ProcessOut])
async def list_processes(db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "process.read")
    rows = (await db.execute(select(Process))).scalars().all()
    return [
        ProcessOut(id=r.id, title=getattr(r, "title", f"Process #{r.id}"),
                   status=getattr(r, "status", None),
                   assignee_email=getattr(r, "assignee_email", None))
        for r in rows
    ]


@router.post("", response_model=ProcessOut)
async def create_process(body: ProcessIn, db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "process.create")
    # минимальная привязка — используем ваши поля Process
    obj = Process(
        title=body.title,
        status=getattr(Process, "status", None) and "open" or None,
        assignee_email=body.assignee_email,
    )
    db.add(obj); await db.commit(); await db.refresh(obj)
    return ProcessOut(id=obj.id, title=getattr(obj, "title", f"Process #{obj.id}"),
                      status=getattr(obj, "status", None),
                      assignee_email=getattr(obj, "assignee_email", None))
