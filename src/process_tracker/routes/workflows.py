from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models_meta import WorkflowDef
from ._deps import get_db, CurrentUser, require_perm

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class WorkflowDefIn(BaseModel):
    key: str = Field(..., max_length=64)
    version: int = 1
    definition: dict


class WorkflowDefOut(WorkflowDefIn):
    id: int


@router.get("", response_model=List[WorkflowDefOut])
async def list_workflows(db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "workflow.read")
    rows = (await db.execute(select(WorkflowDef))).scalars().all()
    return [WorkflowDefOut(id=r.id, key=r.key, version=r.version, definition=r.definition) for r in rows]


@router.post("", response_model=WorkflowDefOut)
async def create_workflow(body: WorkflowDefIn, db: AsyncSession = Depends(get_db), user=Depends(CurrentUser)):
    require_perm(user, "workflow.create")
    obj = WorkflowDef(key=body.key, version=body.version, definition=body.definition)
    db.add(obj); await db.commit(); await db.refresh(obj)
    return WorkflowDefOut(id=obj.id, key=obj.key, version=obj.version, definition=obj.definition)
