"""
Process Tracker package marker.

Запуск UI:
  - python -m process_tracker.main
  - из кода: process_tracker.run_app()
"""
from __future__ import annotations

try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError  # type: ignore
except Exception:
    _pkg_version = None  # type: ignore[assignment]

    class PackageNotFoundError(Exception):  # type: ignore[no-redef]
        pass


def _detect_version() -> str:
    # Сначала пытаемся получить версию установленного дистрибутива
    if _pkg_version:
        for dist_name in ("process-tracker", "process_tracker"):
            try:
                return _pkg_version(dist_name)  # type: ignore[misc]
            except PackageNotFoundError:
                continue
    # fallback для разработки из исходников
    return "0.1.0"


__version__ = _detect_version()


def run_app() -> None:
    """Удобный лончер UI без тяжёлого импорта на уровне модуля."""
    from .app import run as _run
    _run()


__all__ = ["__version__", "run_app"]
