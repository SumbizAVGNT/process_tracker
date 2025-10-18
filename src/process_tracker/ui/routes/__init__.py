# src/process_tracker/routes/__init__.py

from __future__ import annotations

from typing import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ..core.config import settings
from .tasks import router as tasks_router
from .ws import router as ws_router


def build_api() -> FastAPI:
    app = FastAPI(title="Process Tracker API", version="0.1.0")

    # ---------- Middlewares ----------
    # CORS
    origins: Sequence[str] = settings.cors_origins or []
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # GZip для ответов
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Health
    @app.get("/health", tags=["system"])
    async def health():
        return {"ok": True}

    # ---------- Routers ----------
    app.include_router(tasks_router, prefix="/api", tags=["tasks"])
    app.include_router(ws_router, tags=["ws"])

    return app
