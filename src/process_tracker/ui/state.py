# src/process_tracker/ui/state.py
"""
Глобальное состояние UI (клиентская часть Flet).

- Держим признак аутентификации, email пользователя, роли и права
- Утилиты для проверки ролей/прав с поддержкой wildcard (`task.*`, `admin.*`)
- Примитивные set_auth()/clear_auth() для экранов login/logout
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


def _perm_match(perm: str, granted: set[str]) -> bool:
    """
    Проверка права с поддержкой шаблонов:
      - точное совпадение: "task.create"
      - подстановки: "task.*"
      - суперправо: "admin.*"
    """
    if perm in granted:
        return True
    # task.create -> task.*
    parts = perm.split(".")
    for i in range(len(parts), 0, -1):
        star = ".".join(parts[: i - 1] + ["*"])
        if star in granted:
            return True
    # глобальная маска
    return "*.*" in granted or "*" in granted or "admin.*" in granted


@dataclass
class AppState:
    # Авторизация
    user_email: str | None = None
    is_authenticated: bool = False

    # RBAC
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)

    # Произвольный UI-контекст (можно использовать страницами)
    ctx: dict = field(default_factory=dict)

    # ---------- RBAC helpers ----------

    def has_role(self, role: str) -> bool:
        r = (role or "").strip().lower()
        return r in (x.lower() for x in self.roles)

    def can(self, perm: str) -> bool:
        p = (perm or "").strip().lower()
        if not p:
            return False
        return _perm_match(p, {x.lower() for x in self.permissions})

    # ---------- Auth helpers ----------

    def set_auth(
        self,
        *,
        email: str,
        roles: Iterable[str] | None = None,
        permissions: Iterable[str] | None = None,
    ) -> None:
        self.user_email = (email or "").strip()
        self.is_authenticated = True
        if roles is not None:
            self.roles = list(dict.fromkeys([r.strip() for r in roles if r and r.strip()]))  # uniq, keep order
        if permissions is not None:
            self.permissions = {p.strip() for p in permissions if p and p.strip()}

    def clear_auth(self) -> None:
        self.user_email = None
        self.is_authenticated = False
        self.roles.clear()
        self.permissions.clear()
        # Не трогаем ctx — это общий кэш UI


# Синглтон состояния приложения
state = AppState()
