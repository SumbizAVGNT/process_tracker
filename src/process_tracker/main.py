# src/process_tracker/main.py
from __future__ import annotations

import sys
from pathlib import Path


def _import_run():
    """
    Корректно импортирует run() как при запуске:
      - python -m process_tracker.main   (из корня проекта)
      - python src/process_tracker/main.py  (прямой запуск файла)
    """
    if __package__ in (None, ""):
        # Добавляем .../src в sys.path для src-layout
        src_dir = Path(__file__).resolve().parents[1]  # .../src
        p = str(src_dir)
        if p not in sys.path:
            sys.path.insert(0, p)
        from process_tracker.app import run as _run  # type: ignore
        return _run
    else:
        from .app import run as _run
        return _run


def run():
    _import_run()()


if __name__ == "__main__":
    run()
