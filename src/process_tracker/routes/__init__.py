from __future__ import annotations

from typing import Sequence
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ..core.config import settings
from .rate_limit import rate_limit
try:
    from ..security.auth import require
    _guard_read_tasks = [Depends(require("tasks.read"))]
    _guard_manage_templates = [Depends(require("templates.manage"))]
except Exception:
    _guard_read_tasks = []
    _guard_manage_templates = []

API_PREFIX = "/api/v1"

def build_api() -> FastAPI:
    app = FastAPI(title="Process Tracker API", version="0.1.0")

    origins: Sequence[str] = settings.cors_origins or []
    if origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=list(origins),
            allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
        )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.get("/", tags=["system"])
    async def root(): return {"ok": True, "name": "process-tracker", "version": app.version}

    @app.get("/health", tags=["system"])
    async def health(): return {"ok": True}

    def add(router, *tags, guards=None):
        try:
            app.include_router(router, prefix=API_PREFIX, tags=list(tags),
                               dependencies=[Depends(rate_limit)] + (guards or []))
        except Exception:
            pass

    # core routers
    from .tasks import router as tasks_router
    add(tasks_router, "tasks", guards=_guard_read_tasks)

    from .processes import router as processes_router
    add(processes_router, "processes")

    from .forms import router as forms_router
    add(forms_router, "forms")

    from .workflows import router as workflows_router
    add(workflows_router, "workflows")

    from .templates import router as templates_router
    add(templates_router, "templates", guards=_guard_manage_templates)

    from .webhooks import router as webhooks_router
    add(webhooks_router, "webhooks")

    from .views import router as views_router
    add(views_router, "views")

    from .files import router as files_router
    add(files_router, "files")

    # new
    from .auth import router as auth_router
    add(auth_router, "auth")

    from .users import router as users_router
    add(users_router, "users")

    from .attachments import router as attachments_router
    add(attachments_router, "attachments")

    from .audit import router as audit_router
    add(audit_router, "audit")

    # SSE events (без rate-limit — можно оставить, но лучше без)
    try:
        from .events import router as events_router
        app.include_router(events_router, prefix=API_PREFIX, tags=["events"])
    except Exception:
        pass

    # websockets
    try:
        from .ws import router as ws_router
        app.include_router(ws_router, tags=["ws"])
    except Exception:
        pass

    return app
