from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..services.process_service import ProcessService

router = APIRouter(tags=["processes"])  # префикс /api/v1 в build_api()

# ----- Schemas -----

class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int

class ProcessIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    status: str = Field(default="new", max_length=50)

class ProcessOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProcessPage(BaseModel):
    items: List[ProcessOut]
    meta: PageMeta

# ----- DI -----

def _svc() -> ProcessService:
    return ProcessService()

# ----- Handlers -----

@router.get("/processes", response_model=ProcessPage)
async def list_processes(
    svc: ProcessService = Depends(_svc),
    q: Optional[str] = Query(None, description="Поиск по заголовку/описанию"),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    # ProcessService сейчас отдаёт последние N — заберём с запасом и отфильтруем на уровне API
    items = await svc.list_recent(limit=limit + offset + 200)  # небольшой запас
    if q:
        ql = q.lower()
        items = [i for i in items if ql in (getattr(i, "title", "") or "").lower()
                 or ql in (getattr(i, "description", "") or "").lower()]
    if status_filter:
        sf = status_filter.lower()
        items = [i for i in items if (getattr(i, "status", "new") or "").lower() == sf]

    total = len(items)
    sliced = items[offset: offset + limit]

    out = [
        ProcessOut.model_validate(
            {
                "id": i.id,
                "title": i.title,
                "description": getattr(i, "description", None),
                "status": getattr(i, "status", "new"),
                "created_at": getattr(i, "created_at", None),
                "updated_at": getattr(i, "updated_at", None),
            }
        )
        for i in sliced
    ]
    return ProcessPage(items=out, meta=PageMeta(total=total, limit=limit, offset=offset))


@router.get("/processes/{proc_id}", response_model=ProcessOut)
async def get_process(proc_id: int, svc: ProcessService = Depends(_svc)):
    items = await svc.list_recent(limit=500)  # временно
    i = next((x for x in items if getattr(x, "id", None) == proc_id), None)
    if not i:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="process not found")
    return ProcessOut(
        id=i.id, title=i.title, description=getattr(i, "description", None),
        status=getattr(i, "status", "new"),
        created_at=getattr(i, "created_at", None),
        updated_at=getattr(i, "updated_at", None),
    )


@router.post("/processes", response_model=ProcessOut, status_code=status.HTTP_201_CREATED)
async def create_process(body: ProcessIn, svc: ProcessService = Depends(_svc)):
    item = await svc.create(body.title.strip(), body.description, body.status)
    return ProcessOut(
        id=item.id,
        title=item.title,
        description=getattr(item, "description", None),
        status=getattr(item, "status", "new"),
        created_at=getattr(item, "created_at", None),
        updated_at=getattr(item, "updated_at", None),
    )
