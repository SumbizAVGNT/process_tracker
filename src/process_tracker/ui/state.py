from __future__ import annotations
"""
Глобальное состояние UI (Flet).
- Авторизация: email, is_authenticated
- RBAC: roles, permissions (+ wildcard: "task.*", "admin.*")
- Контекст: произвольный словарь для межстраничного обмена
"""

from dataclasses import dataclass, field
from typing import Iterable


def _perm_match(perm: str, granted: set[str]) -> bool:
    """
    Проверка права с поддержкой шаблонов:
      - точное совпадение: "task.create"
      - подстановки: "task.*"
      - суперправо: "admin.*"
      - универсальная маска: "*.*" или "*"
    """
    p = perm.strip().lower()
    if p in granted:
        return True

    parts = p.split(".")
    for i in range(len(parts), 0, -1):
        # "task.create" -> "task.*" -> "*"
        star = ".".join(parts[: i - 1] + ["*"]) if i > 1 else "*"
        if star in granted:
            return True

    return "*.*" in granted or "*" in granted or "admin.*" in granted


@dataclass
class AppState:
    # Авторизация
    user_email: str | None = None
    is_authenticated: bool = False

    # RBAC
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)

    # Общий UI-контекст
    ctx: dict = field(default_factory=dict)

    # ---------- RBAC helpers ----------

    def has_role(self, role: str) -> bool:
        r = (role or "").strip().lower()
        return any(r == x.strip().lower() for x in self.roles)

    def can(self, perm: str) -> bool:
        p = (perm or "").strip().lower()
        if not p:
            return False
        return _perm_match(p, {x.strip().lower() for x in self.permissions})

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
            self.roles = list(dict.fromkeys([r.strip() for r in roles if r and r.strip()]))  # uniq
        if permissions is not None:
            self.permissions = {p.strip() for p in permissions if p and p.strip()}

    def clear_auth(self) -> None:
        self.user_email = None
        self.is_authenticated = False
        self.roles.clear()
        self.permissions.clear()
        # ctx не трогаем — может содержать кэш UI/настроек


# Синглтон состояния приложения
state = AppState()
