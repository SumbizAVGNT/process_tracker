# src/process_tracker/main.py
from __future__ import annotations

import sys
from pathlib import Path


def _import_run():
    """
    Корректно импортирует run() как при запуске:
      - python -m process_tracker.main    (из корня проекта / установленного пакета)
      - python src/process_tracker/main.py  (прямой запуск файла в src-layout)
    """
    # Запуск как одиночный файл: __package__ пустой -> добавляем .../src в sys.path
    if __package__ in (None, ""):
        src_dir = Path(__file__).resolve().parents[1]  # .../src
        p = str(src_dir)
        if p not in sys.path:
            sys.path.insert(0, p)
        # далее импорт как установленного пакета
        from process_tracker.app import run as _run  # type: ignore[attr-defined]
        return _run
    # Обычный пакетный импорт
    from .app import run as _run
    return _run


def run():
    _import_run()()


if __name__ == "__main__":
    run()
