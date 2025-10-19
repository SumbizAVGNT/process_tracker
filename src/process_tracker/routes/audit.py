from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["audit"])

# in-memory журнал
_LOG: list[dict] = []

class AuditIn(BaseModel):
    entity: str = Field(..., pattern="^(task|process)$")
    entity_id: int
    event: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class AuditOut(BaseModel):
    ts: datetime
    entity: str
    entity_id: int
    event: str
    payload: Dict[str, Any]

@router.post("/audit", response_model=AuditOut, status_code=status.HTTP_201_CREATED)
async def add_audit(body: AuditIn):
    rec = {"ts": datetime.utcnow(), **body.model_dump()}
    _LOG.append(rec)
    return AuditOut.model_validate(rec)

@router.get("/audit", response_model=List[AuditOut])
async def list_audit(
    entity: Optional[str] = Query(None, pattern="^(task|process)$"),
    entity_id: Optional[int] = Query(None),
    event: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    items = list(_LOG)[-limit:]
    if entity:
        items = [x for x in items if x["entity"] == entity]
    if entity_id is not None:
        items = [x for x in items if int(x["entity_id"]) == int(entity_id)]
    if event:
        items = [x for x in items if x["event"] == event]
    return [AuditOut.model_validate(x) for x in items]
