from __future__ import annotations
"""
Лёгкая авторизация/автентификация для FastAPI.

Поддерживает два способа:
1) Bearer JWT (HS256), поля payload: sub/email, roles, perms, iat, exp.
2) Dev-заголовки: X-User-Email / X-User-Roles / X-User-Perms
   (строки со списками через запятую).

А также зависимости:
- require(*perms): все перечисленные права
- require_any(*perms): хотя бы одно из прав
- require_role(role): наличие конкретной роли
"""

from dataclasses import dataclass
from typing import Iterable, Set, Optional

from fastapi import Depends, Header, HTTPException, status, Request

from .rbac import can

try:
    from ..core.config import settings  # type: ignore
    # В Settings определён app_secret_key (см. core/config.py)
    SECRET = getattr(settings, "app_secret_key", "dev-secret")
except Exception:
    SECRET = "dev-secret"

# JWT-утилиты (микро-реализация HS256)
try:
    from .jwt import decode as jwt_decode
except Exception:
    def jwt_decode(_t: str, _s: str):  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT unavailable")


def _split_csv(v: Optional[str]) -> Set[str]:
    if not v:
        return set()
    return {x.strip().lower() for x in v.split(",") if x and x.strip()}


def _norm_set(items: Iterable[str | None]) -> Set[str]:
    return {str(x).strip().lower() for x in items if x and str(x).strip()}


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
    # Bearer JWT
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = jwt_decode(token, SECRET)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

        email = payload.get("sub") or payload.get("email")
        roles = payload.get("roles", [])
        perms = payload.get("perms", [])

        # в payload могут приехать как list, так и строка через запятую
        if isinstance(roles, str):
            roles_set = _split_csv(roles)
        else:
            roles_set = _norm_set(roles)

        if isinstance(perms, str):
            perms_set = _split_csv(perms)
        else:
            perms_set = _norm_set(perms)

        return UserContext(email=email, roles=roles_set, permissions=perms_set)

    # Dev-заголовки
    roles = _split_csv(x_user_roles)
    perms = _split_csv(x_user_perms)
    return UserContext(email=(x_user_email or None), roles=roles, permissions=perms)


def require(*perms: str):
    """
    Требует ВСЕ перечисленные права (логическое AND).
    """
    perms_norm = tuple((p or "").strip().lower() for p in perms if p and p.strip())

    async def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        for p in perms_norm:
            if not can(user.permissions, p):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"forbidden: {p}")
        return user

    return _dep


def require_any(*perms: str):
    """
    Требует ХОТЯ БЫ ОДНО из перечисленных прав (логическое OR).
    Пустой список прав пропускает всех.
    """
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
    """
    Требует наличие роли у пользователя.
    """
    role_norm = (role or "").strip().lower()

    async def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(role_norm):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"forbidden: role {role_norm}")
        return user

    return _dep
