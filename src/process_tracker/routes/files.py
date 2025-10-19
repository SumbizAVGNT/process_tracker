from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

try:
    from ..core.config import settings  # type: ignore
    MEDIA_DIR = Path(getattr(settings, "media_root", "./data/uploads")).resolve()
except Exception:
    MEDIA_DIR = Path("./data/uploads").resolve()

router = APIRouter(tags=["files"])

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/files", status_code=status.HTTP_201_CREATED)
async def upload_files(files: List[UploadFile] = File(...)):
    saved = []
    for uf in files:
        # простое имя файла (без директорий)
        name = os.path.basename(uf.filename or "file.bin")
        safe = name.replace("/", "_").replace("\\", "_")
        dst = MEDIA_DIR / safe
        # если существует — добавим индекс
        i = 1
        stem, ext = os.path.splitext(safe)
        while dst.exists():
            dst = MEDIA_DIR / f"{stem}_{i}{ext}"
            i += 1
        content = await uf.read()
        with open(dst, "wb") as f:
            f.write(content)
        saved.append({"filename": dst.name, "size": len(content), "url": f"/api/v1/files/{dst.name}"})
    return {"items": saved}


@router.get("/files/{filename}")
async def get_file(filename: str):
    fp = MEDIA_DIR / filename
    if not fp.exists() or not fp.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")
    return FileResponse(fp)
