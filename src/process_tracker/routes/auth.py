from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ..security.auth import get_current_user, UserContext
from ..security.jwt import encode as jwt_encode

try:
    from ..core.config import settings  # type: ignore
    SECRET = getattr(settings, "secret_key", "dev-secret")
    ACCESS_TTL = int(getattr(settings, "access_ttl_seconds", 3600))
    REFRESH_TTL = int(getattr(settings, "refresh_ttl_seconds", 30 * 24 * 3600))
except Exception:
    SECRET = "dev-secret"
    ACCESS_TTL = 3600
    REFRESH_TTL = 30 * 24 * 3600

router = APIRouter(tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    roles: List[str] = Field(default_factory=list)
    perms: List[str] = Field(default_factory=list)

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TTL

class RefreshIn(BaseModel):
    refresh_token: str

class MeOut(BaseModel):
    email: Optional[str]
    roles: List[str]
    perms: List[str]


@router.post("/auth/login", response_model=TokenOut)
async def login_dev(body: LoginIn):
    """
    DEV: логин по email, сразу выдаём токены (без отправки кода).
    """
    access = jwt_encode({"sub": body.email, "roles": body.roles, "perms": body.perms}, SECRET, exp_seconds=ACCESS_TTL)
    refresh = jwt_encode({"sub": body.email, "type": "refresh"}, SECRET, exp_seconds=REFRESH_TTL)
    return TokenOut(access_token=access, refresh_token=refresh)

@router.post("/auth/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn):
    # тут для простоты НЕ валидируем refresh payload, но можно проверить type == "refresh"
    # и извлечь email из него (нужно decode; в auth.get_current_user это уже есть).
    # Мы не декодим тут для компактности — в реале декодируй refresh и строй access c ролями/правами.
    access = jwt_encode({"sub": "unknown", "roles": [], "perms": []}, SECRET, exp_seconds=ACCESS_TTL)
    return TokenOut(access_token=access, refresh_token=body.refresh_token)

@router.get("/auth/me", response_model=MeOut)
async def me(user: UserContext = Depends(get_current_user)):
    return MeOut(email=user.email, roles=sorted(user.roles), perms=sorted(user.permissions))
