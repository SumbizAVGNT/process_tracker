from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.dal import ProcessRepo

router = APIRouter()

class ProcessIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    status: str = Field(default="new", max_length=40)

class ProcessOut(BaseModel):
    id: int
    name: str
    status: str

@router.get("/processes", response_model=List[ProcessOut])
async def list_processes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = ProcessRepo(session)
    items = await repo.list()
    items = items[offset : offset + limit]
    return [ProcessOut(id=i.id, name=i.name, status=i.status) for i in items]

@router.post("/processes", response_model=ProcessOut, status_code=status.HTTP_201_CREATED)
async def create_process(body: ProcessIn, session: AsyncSession = Depends(get_session)):
    repo = ProcessRepo(session)
    obj = await repo.create(body.name, status=body.status)
    await session.commit()
    return ProcessOut(id=obj.id, name=obj.name, status=obj.status)

class ProcessStatusIn(BaseModel):
    status: str = Field(..., max_length=40)

@router.patch("/processes/{process_id}/status", response_model=ProcessOut)
async def set_process_status(process_id: int, body: ProcessStatusIn, session: AsyncSession = Depends(get_session)):
    repo = ProcessRepo(session)
    updated_id = await repo.set_status(process_id, body.status)
    if not updated_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="process not found")
    await session.commit()
    items = await repo.list()
    obj = next((x for x in items if x.id == process_id), None)
    return ProcessOut(id=obj.id, name=obj.name, status=obj.status)

@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process(process_id: int, session: AsyncSession = Depends(get_session)):
    repo = ProcessRepo(session)
    deleted_id = await repo.remove(process_id)
    if not deleted_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="process not found")
    await session.commit()
    return
