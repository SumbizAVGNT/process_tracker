from __future__ import annotations
"""
Глобальное состояние UI (Flet).
- Авторизация: email, is_authenticated
- RBAC: roles, permissions (+ подстановки: "*", "task.*", "task.view.*")
- Контекст: произвольный словарь для межстраничного обмена
- Слушатели: on_change(callback) для реакции UI на изменение состояния
"""

from dataclasses import dataclass, field, asdict
from typing import Iterable, Callable, Dict, Any, List, Optional


# --------------------------- RBAC helpers ---------------------------

def _norm(s: str | None) -> str:
    return (s or "").strip().lower()

def _perm_match(perm: str, granted: set[str]) -> bool:
    """
    Проверка права с поддержкой шаблонов.
    Поддерживает:
      - точное совпадение:         "task.create"
      - сегментные маски:          "task.*", "*.create", "task.*.edit"
      - универсальные маски:       "*", "*.*"
      - семейство админа:          "admin.*"
    Реализовано симметрично: сравниваем `perm` со всеми шаблонами из `granted`.
    """
    p = _norm(perm)
    if not p:
        return False

    if p in granted:
        return True

    # Быстрые глобальные маски
    if "*" in granted or "*.*" in granted or "admin.*" in granted:
        return True

    p_parts = p.split(".")

    for g in granted:
        g = _norm(g)
        if not g:
            continue
        if g == "*":
            return True
        # "admin.*" → админ на всё
        if g == "admin.*":
            return True

        g_parts = g.split(".")

        # Сравнение по сегментам со звёздочкой как wildcard сегмента.
        # Примеры:
        #   p=task.create.item, g=task.*         → True
        #   p=task.create,      g=*.create      → True
        #   p=task.a.edit,      g=task.*.edit   → True
        max_len = max(len(p_parts), len(g_parts))
        ok = True
        for i in range(max_len):
            pp = p_parts[i] if i < len(p_parts) else ""
            gg = g_parts[i] if i < len(g_parts) else ""
            if gg == "*":
                continue
            if not gg or not pp or gg != pp:
                ok = False
                break
        if ok:
            return True

        # Дополнительно: если шаблон короче и заканчивается на "*"
        if len(g_parts) < len(p_parts) and g_parts and g_parts[-1] == "*":
            # пример: g="task.*" и p="task.create.item" → ок
            head = g_parts[:-1]
            if p_parts[: len(head)] == head:
                return True

    return False


# --------------------------- UI State ---------------------------

@dataclass
class AppState:
    # Авторизация
    user_email: str | None = None
    is_authenticated: bool = False

    # RBAC
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)

    # Общий UI-контекст (для обмена данными между экранами)
    ctx: dict = field(default_factory=dict)

    # Слушатели изменений состояния
    _listeners: List[Callable[["AppState"], None]] = field(default_factory=list, repr=False)

    # ---------- RBAC helpers ----------

    def has_role(self, role: str) -> bool:
        r = _norm(role)
        return any(r == _norm(x) for x in self.roles)

    def can(self, perm: str) -> bool:
        p = _norm(perm)
        if not p:
            return False
        granted = {_norm(x) for x in self.permissions}
        return _perm_match(p, granted)

    def grant(self, *perms: Iterable[str] | str) -> None:
        """Добавить права пользователю."""
        added: set[str] = set()
        for item in perms:
            if isinstance(item, str):
                added.add(_norm(item))
            else:
                added.update(_norm(x) for x in item)
        self.permissions |= {p for p in added if p}
        self._emit()

    def revoke(self, *perms: Iterable[str] | str) -> None:
        """Убрать права у пользователя."""
        rem: set[str] = set()
        for item in perms:
            if isinstance(item, str):
                rem.add(_norm(item))
            else:
                rem.update(_norm(x) for x in item)
        self.permissions -= {p for p in rem if p}
        self._emit()

    # ---------- Auth helpers ----------

    def set_auth(
        self,
        *,
        email: str,
        roles: Iterable[str] | None = None,
        permissions: Iterable[str] | None = None,
    ) -> None:
        self.user_email = _norm(email)
        self.is_authenticated = True
        if roles is not None:
            self.roles = list(dict.fromkeys([_norm(r) for r in roles if _norm(r)]))  # uniq + normalize
        if permissions is not None:
            self.permissions = {_norm(p) for p in permissions if _norm(p)}
        self._emit()

    def clear_auth(self, *, clear_ctx: bool = False) -> None:
        self.user_email = None
        self.is_authenticated = False
        self.roles.clear()
        self.permissions.clear()
        if clear_ctx:
            self.ctx.clear()
        self._emit()

    @property
    def is_admin(self) -> bool:
        """Быстрый флаг для UI."""
        return self.can("admin.*")

    # ---------- Ctx helpers ----------

    def set_ctx(self, key: str, value: Any) -> None:
        self.ctx[key] = value
        self._emit()

    def get_ctx(self, key: str, default: Any = None) -> Any:
        return self.ctx.get(key, default)

    def pop_ctx(self, key: str, default: Any = None) -> Any:
        val = self.ctx.pop(key, default)
        self._emit()
        return val

    def update_ctx(self, **kwargs: Any) -> None:
        self.ctx.update({k: v for k, v in kwargs.items()})
        self._emit()

    # ---------- Listeners / Events ----------

    def on_change(self, cb: Callable[["AppState"], None]) -> Callable[[], None]:
        """
        Подписаться на изменения состояния.
        Возвращает функцию отписки: unsubscribe = state.on_change(cb)
        """
        if cb not in self._listeners:
            self._listeners.append(cb)

        def _unsub() -> None:
            try:
                self._listeners.remove(cb)
            except ValueError:
                pass

        return _unsub

    def _emit(self) -> None:
        for cb in list(self._listeners):
            try:
                cb(self)
            except Exception:
                # слушатель не должен валить приложение
                pass

    # ---------- Misc ----------

    def to_dict(self) -> Dict[str, Any]:
        """Снапшот состояния (без слушателей)."""
        d = asdict(self)
        d.pop("_listeners", None)
        return d

    def __repr__(self) -> str:  # удобнее дебажить
        auth = "auth" if self.is_authenticated else "anon"
        roles = ",".join(self.roles) or "-"
        perms = len(self.permissions)
        return f"<AppState {auth} email={self.user_email!r} roles=[{roles}] perms={perms} ctx={len(self.ctx)}>"

# Синглтон состояния приложения
state = AppState()

__all__ = ["AppState", "state"]
