from __future__ import annotations
from typing import AsyncGenerator, Iterable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..security.auth import get_current_user, UserContext  # ваша реализация


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as s:
        yield s


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


def require_perm(ctx: UserContext, perm: str) -> None:
    perms = getattr(ctx, "perms", []) or []
    if not _match_perm(perm, perms):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


CurrentUser = get_current_user
