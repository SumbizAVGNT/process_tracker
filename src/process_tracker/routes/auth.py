# src/process_tracker/routes/auth.py
from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
import secrets
import time

# ВАЖНО: префикс ТОЛЬКО "/auth" — общий "/api/v1" добавит сборщик API
router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_TTL = 60 * 60 * 12         # 12h
REFRESH_TTL = 60 * 60 * 24 * 7    # 7d

_TOKENS: Dict[str, Dict[str, Any]] = {}
_REFRESH: Dict[str, Dict[str, Any]] = {}

def _now() -> int:
    return int(time.time())

def _split_any(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    if isinstance(v, (list, tuple, set)):
        return [str(x).strip() for x in v if str(x).strip()]
    return []

class LoginIn(BaseModel):
    email: Optional[str] = Field(default=None, description="Любая строка (dev)")
    roles: List[str] = Field(default_factory=list)
    perms: List[str] = Field(default_factory=list)

    def normalize(self) -> "LoginIn":
        return LoginIn(
            email=(self.email or "").strip() or "dev@local",
            roles=_split_any(self.roles),
            perms=_split_any(self.perms),
        )

class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TTL

def _issue_tokens(user: Dict[str, Any]) -> TokensOut:
    access = "dev-" + secrets.token_urlsafe(24)
    refresh = "devr-" + secrets.token_urlsafe(24)
    now = _now()
    _TOKENS[access] = {**user, "exp": now + ACCESS_TTL}
    _REFRESH[refresh] = {**user, "exp": now + REFRESH_TTL}
    return TokensOut(access_token=access, refresh_token=refresh)

def _user_from_bearer(authorization: Optional[str]) -> Dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    u = _TOKENS.get(token)
    if not u:
        return None
    if u.get("exp", 0) < _now():
        _TOKENS.pop(token, None)
        return None
    return u

@router.post("/login", response_model=TokensOut)
async def login_dev(body: LoginIn):
    b = body.normalize()
    user_ctx = {
        "email": b.email,
        "roles": b.roles or ["dev"],
        "perms": set(b.perms or ["*"]),
    }
    return _issue_tokens(user_ctx)

@router.get("/me")
async def me(authorization: Optional[str] = Header(default=None)):
    u = _user_from_bearer(authorization)
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return {"email": u["email"], "roles": u["roles"], "perms": sorted(list(u["perms"]))}

@router.post("/refresh", response_model=TokensOut)
async def refresh_token(refresh_token: str):
    data = _REFRESH.get(refresh_token)
    if not data or data.get("exp", 0) < _now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
    user_ctx = {"email": data["email"], "roles": data["roles"], "perms": data["perms"]}
    return _issue_tokens(user_ctx)

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        _TOKENS.pop(token, None)
    return {"ok": True}
