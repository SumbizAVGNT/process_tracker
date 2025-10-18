# src/process_tracker/server/__init__.py
"""
Расширяемый серверный модуль.
- Поднимает FastAPI в фоновом потоке (uvicorn).
- Предоставляет registry для расширений (router'ы, middlewares и т.п.).
- Экспортирует удобные функции: start_api_server(), stop_api_server(), is_running(), register_extension().
"""

from __future__ import annotations

import os
import threading
from typing import Callable, List, Optional

import uvicorn
from fastapi import FastAPI

# Надёжный импорт сборщика API (работает и при модульном, и при скриптовом запуске)
try:
    from ..routes import build_api  # типичный случай
except Exception:  # noqa: BLE001
    # fallback на абсолютный импорт, если относительный недоступен
    from process_tracker.routes import build_api  # type: ignore


# -------- Registry для расширений --------
_Extension = Callable[[FastAPI], None]
_extensions: List[_Extension] = []


def register_extension(func: _Extension) -> None:
    """
    Зарегистрировать расширение, которое получит FastAPI-приложение
    и сможет навесить роуты, middlewares, события и т.д.
    Вызывать ДО старта сервера.
    """
    _extensions.append(func)


# -------- Внутренние объекты и guard --------
_app: Optional[FastAPI] = None
_server: Optional[uvicorn.Server] = None
_thread: Optional[threading.Thread] = None
_started = False
_lock = threading.Lock()


def _build_app() -> FastAPI:
    app = build_api()

    # Базовый health-check (на случай, если его нет в роутерах)
    @app.get("/health", tags=["system"])
    async def health():
        return {"ok": True}

    # Применяем расширения
    for ext in list(_extensions):
        ext(app)

    return app


def start_api_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: str = "info",
) -> None:
    """
    Запустить FastAPI + uvicorn в фоновом потоке.
    Параметры можно задать через ENV: API_HOST, API_PORT.
    Повторный вызов — no-op.
    """
    global _app, _server, _thread, _started

    with _lock:
        if _started:
            return

        host = host or os.getenv("API_HOST", "127.0.0.1")
        port = int(port or os.getenv("API_PORT", "8787"))

        _app = _build_app()
        config = uvicorn.Config(
            _app,
            host=host,
            port=port,
            log_level=log_level,
            lifespan="on",
        )
        _server = uvicorn.Server(config)

        def _run():
            assert _server is not None
            _server.run()

        _thread = threading.Thread(target=_run, name="api-server", daemon=True)
        _thread.start()
        _started = True


def stop_api_server(join: bool = False, timeout: Optional[float] = 5.0) -> None:
    """
    Остановить сервер (graceful). По умолчанию не блокирует вызывающий поток.
    """
    global _server, _thread, _started
    with _lock:
        srv = _server
        th = _thread
        if not _started or srv is None:
            return
        srv.should_exit = True

    if join and th is not None:
        th.join(timeout=timeout)
    with _lock:
        _started = False


def is_running() -> bool:
    with _lock:
        return _started


def get_application() -> FastAPI:
    """
    Вернуть инстанс FastAPI (создаст новый, если ещё не создан).
    Полезно для тестов.
    """
    global _app
    with _lock:
        if _app is None:
            _app = _build_app()
        return _app
