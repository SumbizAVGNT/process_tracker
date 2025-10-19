from __future__ import annotations

import os
from pathlib import Path


def upgrade_head_with_bootstrap() -> None:
    """
    Попытка выполнить `alembic upgrade head`.
    Если alembic/ini не найден — тихо выходим (dev-режим).
    """
    try:
        from alembic import command
        from alembic.config import Config
    except Exception:
        return

    cwd = Path(os.getcwd())
    candidates = [cwd / "alembic.ini", cwd.parent / "alembic.ini"]
    ini_path = next((p for p in candidates if p.is_file()), None)
    if not ini_path:
        return

    cfg = Config(str(ini_path))
    try:
        command.upgrade(cfg, "head")
    except Exception:
        # Не считаем это критичным для запуска
        pass
