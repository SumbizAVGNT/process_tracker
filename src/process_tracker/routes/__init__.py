# src/process_tracker/routes/__init__.py
from __future__ import annotations

from typing import Sequence

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ..core.config import settings
from .rate_limit import rate_limit


def build_api() -> FastAPI:
    """
    Собирает FastAPI-приложение.
    Импорт роутеров выполнен ЛЕНИВО внутри функции, чтобы не ломать импорт пакета,
    даже если tasks.py / processes.py / workflows.py / forms.py ещё не созданы.
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

    # Ленивая регистрация роутеров (+ зависимость rate_limit для REST)
    try:
        from .tasks import router as tasks_router  # type: ignore
        app.include_router(
            tasks_router, prefix="/api", tags=["tasks"],
            dependencies=[Depends(rate_limit)],
        )
    except Exception:
        pass

    try:
        from .processes import router as processes_router  # NEW
        app.include_router(
            processes_router, prefix="/api", tags=["processes"],
            dependencies=[Depends(rate_limit)],
        )
    except Exception:
        pass

    try:
        from .forms import router as forms_router  # type: ignore
        app.include_router(
            forms_router, prefix="/api", tags=["forms"],
            dependencies=[Depends(rate_limit)],
        )
    except Exception:
        pass

    try:
        from .workflows import router as workflows_router  # type: ignore
        app.include_router(
            workflows_router, prefix="/api", tags=["workflows"],
            dependencies=[Depends(rate_limit)],
        )
    except Exception:
        pass

    try:
        from .ws import router as ws_router  # type: ignore
        app.include_router(ws_router, tags=["ws"])  # для WS лимитер не навешиваем
    except Exception:
        pass

    return app
