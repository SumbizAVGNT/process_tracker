# src/process_tracker/main.py
from __future__ import annotations

import os
import sys

def _resolve_run():
    """
    Надёжный импорт run() как при запуске:
      - python -m process_tracker.main
      - python src/process_tracker/main.py
    """
    try:
        # Пакетный запуск
        from .app import run as _run
        return _run
    except Exception:
        # Прямой запуск файла — добавим src в sys.path и импортнём по абсолютному пути
        pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)
        from process_tracker.app import run as _run  # type: ignore
        return _run

def run():
    _resolve_run()()

if __name__ == "__main__":
    run()
