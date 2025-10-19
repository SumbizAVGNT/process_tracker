from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models_meta import ProcessType
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/api/v1/process-types", tags=["process-types"])


class ProcessTypeIn(BaseModel):
    key: str = Field(..., max_length=64)
    name: str
    description: str | None = None


class ProcessTypeOut(ProcessTypeIn):
    id: int


@router.get("", response_model=List[ProcessTypeOut])
async def list_process_types(db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "process_type.read")
    rows = (await db.execute(select(ProcessType))).scalars().all()
    return [ProcessTypeOut(id=r.id, key=r.key, name=r.name, description=r.description) for r in rows]


@router.post("", response_model=ProcessTypeOut)
async def create_process_type(body: ProcessTypeIn, db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "process_type.create")
    obj = ProcessType(key=body.key, name=body.name, description=body.description)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return ProcessTypeOut(id=obj.id, key=obj.key, name=obj.name, description=obj.description)
