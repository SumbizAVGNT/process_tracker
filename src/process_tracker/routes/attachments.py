from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from pydantic import BaseModel

try:
    from ..core.config import settings  # type: ignore
    MEDIA_DIR = Path(getattr(settings, "media_root", "./data/uploads")).resolve() / "attachments"
except Exception:
    MEDIA_DIR = Path("./data/uploads/attachments").resolve()

router = APIRouter(tags=["attachments"])
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

import itertools
_ids = itertools.count(1)
_STORE: dict[int, dict] = {}

class AttachmentOut(BaseModel):
    id: int
    entity: str
    entity_id: int
    filename: str
    size: int
    url: str
    created_at: datetime

@router.post("/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    entity: str = Query(..., pattern="^(task|process)$"),
    entity_id: int = Query(..., ge=1),
    file: UploadFile = File(...),
):
    name = os.path.basename(file.filename or "file.bin")
    safe = name.replace("/", "_").replace("\\", "_")
    dst = MEDIA_DIR / safe
    i = 1
    stem, ext = os.path.splitext(safe)
    while dst.exists():
        dst = MEDIA_DIR / f"{stem}_{i}{ext}"
        i += 1
    content = await file.read()
    with open(dst, "wb") as f:
        f.write(content)
    aid = next(_ids)
    rec = {
        "id": aid,
        "entity": entity,
        "entity_id": entity_id,
        "filename": dst.name,
        "size": len(content),
        "url": f"/api/v1/files/{dst.name}",  # реиспользуем files.py
        "created_at": datetime.utcnow(),
    }
    _STORE[aid] = rec
    return AttachmentOut.model_validate(rec)

@router.get("/attachments", response_model=List[AttachmentOut])
async def list_attachments(entity: Optional[str] = Query(None), entity_id: Optional[int] = Query(None)):
    items = list(_STORE.values())
    if entity:
        items = [x for x in items if x["entity"] == entity]
    if entity_id:
        items = [x for x in items if int(x["entity_id"]) == int(entity_id)]
    return [AttachmentOut.model_validate(x) for x in items]

@router.delete("/attachments/{att_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(att_id: int):
    rec = _STORE.pop(att_id, None)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="attachment not found")
    # файл оставляем (можно удалить при желании)
    return
