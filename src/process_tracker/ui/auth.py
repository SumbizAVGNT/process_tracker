from __future__ import annotations

from typing import Iterable

from .state import state
from .services.api import api  # ваш обёрточный клиент к REST API


async def sign_in(email: str, *, roles: Iterable[str] = (), perms: Iterable[str] = ()) -> None:
    """
    Dev-login через наш /auth/login:
      - получает пару токенов
      - кладёт access_token в api-клиент
      - подтягивает /auth/me и применяет в state
    """
    tokens = await api.login_dev(email, list(roles), list(perms))
    api.set_token(tokens["access_token"])
    me = await api.me()
    state.set_auth(
        email=str(me.get("email") or email),
        roles=me.get("roles") or [],
        permissions=me.get("perms") or [],
    )
    state.set_ctx("auth", {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]})


async def sign_out() -> None:
    """
    Выход: сброс токена в api-клиенте и очистка state.
    """
    try:
        await api.logout()
    except Exception:
        # в dev-режиме ручка может отсутствовать — игнорируем
        pass
    api.set_token(None)
    state.clear_auth()
    state.set_ctx("auth", None)
