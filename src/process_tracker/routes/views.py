from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["views"])

# --- сервис (фоллбек) ---
try:
    from ..services.views_service import ViewsService  # type: ignore
except Exception:
    import itertools
    class ViewsService:  # type: ignore
        _id = itertools.count(1)
        def __init__(self) -> None:
            self._store: dict[int, dict] = {}
        async def list(self, resource: Optional[str] = None) -> list[dict]:
            vals = list(self._store.values())
            return [v for v in vals if resource is None or v.get("resource") == resource]
        async def get(self, view_id: int) -> dict:
            if view_id not in self._store: raise KeyError
            return self._store[view_id]
        async def create(self, name: str, resource: str, query: dict, layout: str, meta: dict | None) -> dict:
            i = next(self._id)
            self._store[i] = {"id": i, "name": name, "resource": resource, "query": query,
                              "layout": layout, "meta": meta or {}, "created_at": datetime.utcnow().isoformat()}
            return self._store[i]
        async def update(self, view_id: int, patch: dict) -> dict:
            if view_id not in self._store: raise KeyError
            self._store[view_id].update(patch)
            return self._store[view_id]
        async def delete(self, view_id: int) -> bool:
            return self._store.pop(view_id, None) is not None

# --- Schemas ---
class ViewIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    resource: str = Field(..., pattern="^(tasks|processes)$")
    query: Dict[str, Any] = Field(default_factory=dict)  # фильтры, сортировки и т.д.
    layout: str = Field("list", pattern="^(list|kanban|calendar|gantt)$")
    meta: Dict[str, Any] = Field(default_factory=dict)   # колонки, swimlanes, группировки

class ViewPatch(BaseModel):
    name: Optional[str] = None
    resource: Optional[str] = Field(default=None, pattern="^(tasks|processes)$")
    query: Optional[Dict[str, Any]] = None
    layout: Optional[str] = Field(default=None, pattern="^(list|kanban|calendar|gantt)$")
    meta: Optional[Dict[str, Any]] = None

class ViewOut(BaseModel):
    id: int
    name: str
    resource: str
    query: Dict[str, Any]
    layout: str
    meta: Dict[str, Any]
    created_at: Optional[datetime] = None

def _svc() -> ViewsService:
    return ViewsService()

# --- Handlers ---
@router.get("/views", response_model=List[ViewOut])
async def list_views(resource: Optional[str] = Query(None, pattern="^(tasks|processes)$"), svc: ViewsService = Depends(_svc)):
    items = await svc.list(resource=resource)
    return [ViewOut.model_validate(i) for i in items]

@router.get("/views/{view_id}", response_model=ViewOut)
async def get_view(view_id: int, svc: ViewsService = Depends(_svc)):
    try:
        i = await svc.get(view_id)
        return ViewOut.model_validate(i)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="view not found")

@router.post("/views", response_model=ViewOut, status_code=status.HTTP_201_CREATED)
async def create_view(body: ViewIn, svc: ViewsService = Depends(_svc)):
    i = await svc.create(body.name, body.resource, body.query, body.layout, body.meta)
    return ViewOut.model_validate(i)

@router.patch("/views/{view_id}", response_model=ViewOut)
async def patch_view(view_id: int, body: ViewPatch, svc: ViewsService = Depends(_svc)):
    try:
        i = await svc.update(view_id, {k: v for k, v in body.model_dump(exclude_none=True).items()})
        return ViewOut.model_validate(i)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="view not found")

@router.delete("/views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_view(view_id: int, svc: ViewsService = Depends(_svc)):
    ok = await svc.delete(view_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="view not found")
    return
