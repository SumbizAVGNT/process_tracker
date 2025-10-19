from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["templates"])

# --- сервис (фоллбек) ---
try:
    from ..services.templates_service import TemplatesService  # type: ignore
except Exception:
    import itertools
    class TemplatesService:  # type: ignore
        _id = itertools.count(1)
        def __init__(self) -> None:
            self._store: dict[int, dict] = {}
        async def list(self) -> list[dict]:
            return list(self._store.values())
        async def get(self, template_id: int) -> dict:
            if template_id not in self._store: raise KeyError
            return self._store[template_id]
        async def create(self, key: str, title: str, form_schema: dict | None, workflow_def: dict | None, visibility: str) -> dict:
            i = next(self._id)
            self._store[i] = {"id": i, "key": key, "title": title, "form_schema": form_schema,
                              "workflow_def": workflow_def, "visibility": visibility,
                              "created_at": datetime.utcnow().isoformat()}
            return self._store[i]
        async def update(self, template_id: int, patch: dict) -> dict:
            if template_id not in self._store: raise KeyError
            self._store[template_id].update(patch)
            return self._store[template_id]
        async def delete(self, template_id: int) -> bool:
            return self._store.pop(template_id, None) is not None

# --- Schemas ---
class TemplateIn(BaseModel):
    key: str = Field(..., min_length=2, max_length=100, description="Напр. 'it.incident'")
    title: str = Field(..., min_length=2, max_length=255)
    form_schema: Optional[Dict[str, Any]] = None
    workflow_def: Optional[Dict[str, Any]] = None
    visibility: str = Field(default="private")  # private/org/public

class TemplatePatch(BaseModel):
    key: Optional[str] = None
    title: Optional[str] = None
    form_schema: Optional[Dict[str, Any]] = None
    workflow_def: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None

class TemplateOut(BaseModel):
    id: int
    key: str
    title: str
    form_schema: Optional[Dict[str, Any]] = None
    workflow_def: Optional[Dict[str, Any]] = None
    visibility: str = "private"
    created_at: Optional[datetime] = None

def _svc() -> TemplatesService:
    return TemplatesService()

# --- Handlers ---
@router.get("/templates", response_model=List[TemplateOut])
async def list_templates(q: Optional[str] = Query(None), svc: TemplatesService = Depends(_svc)):
    items = await svc.list()
    if q:
        ql = q.lower()
        items = [x for x in items if ql in x.get("key", "").lower() or ql in x.get("title", "").lower()]
    return [TemplateOut.model_validate(i) for i in items]

@router.get("/templates/{template_id}", response_model=TemplateOut)
async def get_template(template_id: int, svc: TemplatesService = Depends(_svc)):
    try:
        i = await svc.get(template_id)
        return TemplateOut.model_validate(i)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template not found")

@router.post("/templates", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(body: TemplateIn, svc: TemplatesService = Depends(_svc)):
    i = await svc.create(body.key, body.title, body.form_schema, body.workflow_def, body.visibility)
    return TemplateOut.model_validate(i)

@router.patch("/templates/{template_id}", response_model=TemplateOut)
async def patch_template(template_id: int, body: TemplatePatch, svc: TemplatesService = Depends(_svc)):
    try:
        i = await svc.update(template_id, {k: v for k, v in body.model_dump(exclude_none=True).items()})
        return TemplateOut.model_validate(i)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template not found")

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, svc: TemplatesService = Depends(_svc)):
    ok = await svc.delete(template_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template not found")
    return
