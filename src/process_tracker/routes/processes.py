from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from ..services.process_service import ProcessService

router = APIRouter(tags=["processes"])  # префикс /api навешивается в build_api()

# ----- Schemas -----

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

# ----- DI -----

def _svc() -> ProcessService:
    # Сервис сам откроет/закроет сессию через AsyncSessionLocal
    return ProcessService()

# ----- Handlers -----

@router.get("/processes", response_model=List[ProcessOut])
async def list_processes(svc: ProcessService = Depends(_svc)):
    items = await svc.list_recent(limit=50)
    return [
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
        for i in items
    ]

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
