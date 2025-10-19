from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Process
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/processes", tags=["processes"])


class ProcessIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "active"


class ProcessOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str


@router.get("", response_model=List[ProcessOut])
async def list_processes(db: AsyncSession = Depends(get_db), user=CurrentUser):  # type: ignore
    require_perm(user, "process.read")
    rows = (await db.execute(select(Process))).scalars().all()
    return [
        ProcessOut(id=r.id, name=r.name, description=r.description, status=r.status)
        for r in rows
    ]


@router.post("", response_model=ProcessOut)
async def create_process(body: ProcessIn, db: AsyncSession = Depends(get_db), user=CurrentUser):  # type: ignore
    require_perm(user, "process.create")
    obj = Process(name=body.name, description=body.description, status=body.status)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return ProcessOut(id=obj.id, name=obj.name, description=obj.description, status=obj.status)
