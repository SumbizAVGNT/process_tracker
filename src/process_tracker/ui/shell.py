from __future__ import annotations

"""
Интерактивная dev-оболочка.

Запуск из корня проекта:
    python -m process_tracker.shell

Доступные имена в окружении:
    settings, engine, AsyncSessionLocal, Base, models, arun, ping

Пример:
    In [1]: arun(ping())
    In [2]: async def demo():
       ...:     async with AsyncSessionLocal() as s:
       ...:         res = await s.execute(text("select 42"))
       ...:         print(res.scalar())
       ...: 
    In [3]: arun(demo())
"""

# --- shim для прямого запуска файла из src/ ---
import sys
from pathlib import Path

if __package__ in (None, ""):
    file = Path(__file__).resolve()
    src_dir = file.parents[1]  # .../src
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

import asyncio
import code
from typing import Any

from process_tracker.core.config import settings
from process_tracker.db.session import AsyncSessionLocal, engine
from process_tracker.db.models import Base
from process_tracker import db as models  # пакет с моделями
from sqlalchemy import text


def arun(awaitable):
    """
    Выполнить awaitable из REPL.
    - Если уже в цикле (IPython с asyncio) — поднимет исключение.
    - Иначе выполнит в новом цикле.
    """
    try:
        asyncio.get_running_loop()
        raise RuntimeError("Already in running loop, use `await` directly.")
    except RuntimeError:
        return asyncio.run(awaitable)


async def ping() -> bool:
    """
    Простейшая проверка соединения с БД.
    """
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT 1"))
        return bool(res.scalar())


def _banner() -> str:
    return (
        "Process Tracker shell\n"
        f" DB: {settings.db_url}\n"
        " Names: settings, engine, AsyncSessionLocal, Base, models, arun, ping\n"
    )


def main() -> None:
    ns: dict[str, Any] = {
        "settings": settings,
        "engine": engine,
        "AsyncSessionLocal": AsyncSessionLocal,
        "Base": Base,
        "models": models,
        "arun": arun,
        "ping": ping,
        "text": text,
    }

    # IPython, если доступен
    try:
        from IPython import embed  # type: ignore
        embed(user_ns=ns, banner1=_banner())
        return
    except Exception:
        pass

    # stdlib REPL как fallback
    console = code.InteractiveConsole(locals=ns)
    console.interact(banner=_banner())


if __name__ == "__main__":
    main()
