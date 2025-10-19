from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Set, Optional

from fastapi import Depends, Header, HTTPException, status, Request

from .rbac import can
try:
    from ..core.config import settings  # type: ignore
    SECRET = getattr(settings, "secret_key", "dev-secret")
except Exception:
    SECRET = "dev-secret"

try:
    from .jwt import decode as jwt_decode
except Exception:
    def jwt_decode(_t: str, _s: str):  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT unavailable")


@dataclass(frozen=True)
class UserContext:
    email: Optional[str]
    roles: Set[str]
    permissions: Set[str]

    def can(self, perm: str) -> bool:
        return can(self.permissions, perm)

    def has_role(self, role: str) -> bool:
        r = (role or "").strip().lower()
        return any(r == x for x in self.roles)


async def get_current_user(
    request: Request,
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_user_roles: Optional[str] = Header(None, alias="X-User-Roles"),
    x_user_perms: Optional[str] = Header(None, alias="X-User-Perms"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> UserContext:
    """
    1) Если есть Bearer — парсим JWT.
    2) Иначе — заголовки X-User-* (dev-режим).
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = jwt_decode(token, SECRET)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        email = payload.get("sub") or payload.get("email")
        roles = {r.strip().lower() for r in payload.get("roles", []) if r and str(r).strip()}
        perms = {p.strip().lower() for p in payload.get("perms", []) if p and str(p).strip()}
        return UserContext(email=email, roles=roles, permissions=perms)

    roles = {r.strip().lower() for r in (x_user_roles or "").split(",") if r and r.strip()}
    perms = {p.strip().lower() for p in (x_user_perms or "").split(",") if p and p.strip()}
    return UserContext(email=(x_user_email or None), roles=roles, permissions=perms)


def require(*perms: str):
    perms_norm = tuple((p or "").strip().lower() for p in perms if p and p.strip())

    async def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        for p in perms_norm:
            if not can(user.permissions, p):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"forbidden: {p}")
        return user

    return _dep


def require_any(*perms: str):
    perms_norm = tuple((p or "").strip().lower() for p in perms if p and p.strip())

    async def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not perms_norm:
            return user
        ok = any(can(user.permissions, p) for p in perms_norm)
        if not ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"forbidden: any of {perms_norm}")
        return user

    return _dep


def require_role(role: str):
    role_norm = (role or "").strip().lower()

    async def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(role_norm):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"forbidden: role {role_norm}")
        return user

    return _dep
