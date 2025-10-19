from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


# Универсальный JSON-тип:
#  - PostgreSQL → JSONB
#  - остальные диалекты → JSON (обычно текст с функциями json1 у SQLite)
JSON_AUTO = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


# Компиляция JSONB под SQLite (иные диалекты просто используют нативный механизм)
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw) -> str:
    # SQLite не знает тип JSONB, рендерим как JSON
    return "JSON"


def strip_postgres_jsonb_cast(expr: sa.sql.elements.TextClause | None):
    """
    Если server_default содержит '::jsonb', вернём TextClause без этого суффикса.
    Иначе вернём как есть.
    """
    if expr is None:
        return None
    try:
        txt = str(expr.text if hasattr(expr, "text") else expr)
        if "::jsonb" in txt:
            return sa.text(txt.replace("::jsonb", ""))
    except Exception:
        pass
    return expr
