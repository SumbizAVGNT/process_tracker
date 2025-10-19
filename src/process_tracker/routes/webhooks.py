from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter(tags=["webhooks"])

# --- попытка взять реальный сервис / отправку, с фоллбеком ---
try:
    from ..services.webhooks_service import WebhooksService  # type: ignore
except Exception:  # in-memory fallback
    import itertools
    class WebhooksService:  # type: ignore
        _id = itertools.count(1)
        def __init__(self) -> None:
            self._store: dict[int, dict] = {}
        async def list(self) -> list[dict]:
            return list(self._store.values())
        async def get(self, hook_id: int) -> dict:
            if hook_id not in self._store: raise KeyError
            return self._store[hook_id]
        async def create(self, url: str, events: list[str], secret: str | None, is_active: bool) -> dict:
            i = next(self._id)
            self._store[i] = {"id": i, "url": url, "events": events, "secret": secret, "is_active": is_active,
                              "created_at": datetime.utcnow().isoformat()}
            return self._store[i]
        async def update(self, hook_id: int, patch: dict) -> dict:
            if hook_id not in self._store: raise KeyError
            self._store[hook_id].update(patch)
            return self._store[hook_id]
        async def delete(self, hook_id: int) -> bool:
            return self._store.pop(hook_id, None) is not None

try:
    from ..events.bus import send_webhook  # type: ignore
except Exception:
    import httpx, json, hmac, hashlib
    async def send_webhook(url: str, payload: dict, secret: str | None = None) -> None:  # type: ignore
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["X-Signature-SHA256"] = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        async with httpx.AsyncClient(timeout=10) as cli:
            await cli.post(url, content=body, headers=headers)

# --- Schemas ---

class WebhookIn(BaseModel):
    url: HttpUrl
    events: List[str] = Field(default_factory=lambda: ["*"])
    secret: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True

class WebhookOut(BaseModel):
    id: int
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

class WebhookPatch(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None

class WebhookTestIn(BaseModel):
    event: str = Field(..., description="Имя события, например 'task.created'")
    payload: Dict[str, Any] = Field(default_factory=dict)

def _svc() -> WebhooksService:
    return WebhooksService()

# --- Handlers ---

@router.get("/webhooks", response_model=List[WebhookOut])
async def list_webhooks(svc: WebhooksService = Depends(_svc)):
    hooks = await svc.list()
    return [WebhookOut.model_validate(h) for h in hooks]

@router.get("/webhooks/{hook_id}", response_model=WebhookOut)
async def get_webhook(hook_id: int, svc: WebhooksService = Depends(_svc)):
    try:
        h = await svc.get(hook_id)
        return WebhookOut.model_validate(h)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook not found")

@router.post("/webhooks", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(body: WebhookIn, svc: WebhooksService = Depends(_svc)):
    h = await svc.create(body.url, body.events, body.secret, body.is_active)
    return WebhookOut.model_validate(h)

@router.patch("/webhooks/{hook_id}", response_model=WebhookOut)
async def patch_webhook(hook_id: int, body: WebhookPatch, svc: WebhooksService = Depends(_svc)):
    try:
        h = await svc.update(hook_id, {k: v for k, v in body.model_dump(exclude_none=True).items()})
        return WebhookOut.model_validate(h)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook not found")

@router.delete("/webhooks/{hook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(hook_id: int, svc: WebhooksService = Depends(_svc)):
    ok = await svc.delete(hook_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook not found")
    return

@router.post("/webhooks/{hook_id}/test", status_code=status.HTTP_202_ACCEPTED)
async def test_webhook(hook_id: int, body: WebhookTestIn, svc: WebhooksService = Depends(_svc)):
    try:
        h = await svc.get(hook_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook not found")
    if not h.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webhook is inactive")
    await send_webhook(h["url"], {"event": body.event, "data": body.payload}, h.get("secret"))
    return {"ok": True}
