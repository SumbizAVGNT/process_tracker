# src/process_tracker/main.py
from __future__ import annotations

import os
import sys
import importlib
from pathlib import Path
from types import ModuleType
from typing import Callable


def _clean_sys_path() -> None:
    """
    1) Гарантируем, что в sys.path есть <project>/src (и он стоит ПЕРВЫМ).
    2) Убираем потенциально ломающие записи типа .../src/process_tracker.
    """
    this_file = Path(__file__).resolve()
    pkg_dir = this_file.parent           # .../src/process_tracker
    src_dir = pkg_dir.parent             # .../src
    proj_dir = src_dir.parent            # .../

    # 1) src – в начало sys.path
    src_s = str(src_dir)
    if src_s in sys.path:
        sys.path.remove(src_s)
    sys.path.insert(0, src_s)

    # 2) убрать .../src/process_tracker из sys.path (мешает абсолютным импортам)
    bad = str(pkg_dir)
    sys.path[:] = [p for p in sys.path if Path(p).resolve() != pkg_dir]

    # На всякий случай: рабочую директорию ставим в корень проекта
    try:
        os.chdir(proj_dir)
    except Exception:
        pass


def _try_import_run() -> Callable[[], None]:
    """
    Возвращает функцию run() из process_tracker.app.
    Пытается несколькими способами и прокидывает исходный traceback при ошибке.
    """
    # Вариант А: обычный пакетный импорт
    try:
        mod = importlib.import_module("process_tracker.app")
        run = getattr(mod, "run")
        if callable(run):
            return run  # type: ignore[return-value]
    except Exception as e_a:
        err_a = e_a  # запомним

    # Вариант B: если запускается как пакет внутри src-layout
    try:
        from .app import run as run_rel  # type: ignore[no-redef]
        return run_rel
    except Exception as e_b:
        err_b = e_b  # запомним

    # Если дошли сюда — оба способа не сработали
    msg = (
        "Не удалось импортировать process_tracker.app:run.\n\n"
        "Попробуйте запустить как пакет:\n"
        "  python -m process_tracker.main\n\n"
        "Или убедитесь, что добавлен каталог 'src' в PYTHONPATH.\n\n"
        f"sys.path:\n  " + "\n  ".join(sys.path) + "\n\n"
        "Оригинальные ошибки импорта:\n"
        f"A) import process_tracker.app -> {repr(err_a)}\n"
        f"B) from .app import run      -> {repr(err_b)}\n"
    )
    raise ImportError(msg)


def _import_run() -> Callable[[], None]:
    _clean_sys_path()
    return _try_import_run()


def run() -> None:
    _import_run()()


if __name__ == "__main__":
    run()
