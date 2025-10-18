# src/process_tracker/routes/__init__.py
from __future__ import annotations

from typing import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ...core.config import settings


def build_api() -> FastAPI:
    """
    Собирает FastAPI-приложение.
    Импорт роутеров выполнен ЛЕНИВО внутри функции, чтобы не ломать импорт пакета,
    даже если tasks.py / ws.py ещё не созданы.
    """
    app = FastAPI(title="Process Tracker API", version="0.1.0")

    # Middlewares
    origins: Sequence[str] = settings.cors_origins or []
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.get("/health", tags=["system"])
    async def health():
        return {"ok": True}

    # Ленивая регистрация роутеров
    try:
        from .tasks import router as tasks_router  # type: ignore
        app.include_router(tasks_router, prefix="/api", tags=["tasks"])
    except Exception:
        # Если файла пока нет — просто пропустим; приложение всё равно поднимется
        pass

    try:
        from .ws import router as ws_router  # type: ignore
        app.include_router(ws_router, tags=["ws"])
    except Exception:
        pass

    return app
