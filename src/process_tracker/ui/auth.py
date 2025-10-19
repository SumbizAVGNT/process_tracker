from __future__ import annotations
from typing import Iterable, List

from .state import state
from .services.api import api


async def sign_in(email: str, *, roles: Iterable[str] = (), perms: Iterable[str] = ()) -> None:
    # Dev-login → берём токены
    tokens = await api.login_dev(email, list(roles), list(perms))
    api.set_token(tokens["access_token"])
    # подтянем профиль
    me = await api.me()
    state.set_auth(
        email=str(me.get("email") or email),
        roles=me.get("roles") or [],
        permissions=me.get("perms") or [],
    )
    # сохраним в контекст
    state.set_ctx("auth", {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]})


async def sign_out() -> None:
    api.set_token(None)
    state.clear_auth()
    state.set_ctx("auth", None)
