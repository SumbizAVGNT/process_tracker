from __future__ import annotations

from typing import AsyncGenerator, Iterable, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal

# --- DB session --------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as s:
        yield s


# --- Auth (dev): читаем user из bearer-токена, который выдаёт /auth/login ---

# импортируем помощник из роутера auth (без циклов)
try:
    from .auth import _user_from_bearer as _user_from_bearer  # type: ignore
except Exception:  # fallback: аноним с правом "*"
    def _user_from_bearer(_authorization: Optional[str]):  # type: ignore
        return {"email": "anon@local", "roles": ["dev"], "perms": {"*"}}

async def get_current_user(authorization: Optional[str] = Header(default=None)):
    u = _user_from_bearer(authorization)
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return u

CurrentUser = Depends(get_current_user)


# --- permission helpers ------------------------------------------------------

def _match_perm(perm: str, granted: Iterable[str]) -> bool:
    p = (perm or "").strip().lower()
    g = {x.strip().lower() for x in granted or []}
    if p in g:
        return True
    parts = p.split(".")
    for i in range(len(parts), 0, -1):
        star = ".".join(parts[: i - 1] + ["*"]) if i > 1 else "*"
        if star in g:
            return True
    return "admin.*" in g or "*" in g


def require_perm(ctx: dict, perm: str) -> None:
    perms = set(ctx.get("perms") or [])
    if not _match_perm(perm, perms):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
