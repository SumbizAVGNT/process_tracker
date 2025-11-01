"""
Расширяемый серверный модуль.
- Поднимает FastAPI в фоновом потоке (uvicorn).
- Registry для расширений (router'ы, middlewares и т.п.).
- Старт/стоп/проверка состояния.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable, List, Optional

import uvicorn
from fastapi import FastAPI

# мягкая зависимость на наш логгер/настройки
try:
    from ..core.logging import get_logger
    from ..core.config import settings  # type: ignore
    _LOGGER = get_logger("api-server")
except Exception:  # pragma: no cover
    import logging
    _LOGGER = logging.getLogger("api-server")
    settings = None  # type: ignore[assignment]


# -------- Registry для расширений --------
_Extension = Callable[[FastAPI], None]
_extensions: List[_Extension] = []


def register_extension(func: _Extension) -> None:
    """Зарегистрировать расширение (выполнится на этапе сборки FastAPI)."""
    if func not in _extensions:
        _extensions.append(func)


# -------- Внутренние объекты и guard --------
_app: Optional[FastAPI] = None
_server: Optional[uvicorn.Server] = None
_thread: Optional[threading.Thread] = None
_started = False
_lock = threading.Lock()


def _import_build_api():
    """
    Лениво импортируем сборщик API, чтобы не падать при скриптовом запуске,
    даже если пакет routes ещё не инициализировали/не собрали.
    """
    try:
        # Относительный импорт для пакетного запуска
        from ..routes import build_api  # type: ignore
        return build_api
    except Exception:
        try:
            # Абсолютный импорт при ручной правке sys.path
            from process_tracker.routes import build_api  # type: ignore
            return build_api
        except Exception:
            return None


def _ensure_health_once(app: FastAPI) -> None:
    """Добавить /health, только если его нет."""
    try:
        for r in getattr(app.router, "routes", []):
            if getattr(r, "path", "") == "/health" and "GET" in getattr(r, "methods", set()):
                return
    except Exception:
        pass

    @app.get("/health", tags=["system"])
    async def health():
        return {"ok": True}


def _build_app() -> FastAPI:
    build_api = _import_build_api()

    if build_api is None:
        # Fallback: минимальный API, чтобы приложение не падало
        app = FastAPI(title="Process Tracker API (fallback)", version="0.1.0")
        _ensure_health_once(app)
        for ext in list(_extensions):
            try:
                ext(app)
            except Exception:
                _LOGGER.exception("extension_apply_failed")
        return app

    app = build_api()

    # Базовый health-check (только если его ещё нет)
    _ensure_health_once(app)

    # Применяем расширения
    for ext in list(_extensions):
        try:
            ext(app)
        except Exception:
            _LOGGER.exception("extension_apply_failed")

    return app


def _resolve_host_port(host: Optional[str], port: Optional[int]) -> tuple[str, int, str]:
    """
    Приоритет:
      1) явные аргументы
      2) settings.api_host/api_port + settings.log_level
      3) ENV API_HOST/API_PORT + LOG_LEVEL
      4) дефолты
    """
    default_host = "127.0.0.1"
    default_port = 8787
    default_level = "info"

    cfg_host = getattr(settings, "api_host", None) if settings else None
    cfg_port = getattr(settings, "api_port", None) if settings else None
    cfg_level = getattr(settings, "log_level", None) if settings else None

    env_host = os.getenv("API_HOST")
    env_port = os.getenv("API_PORT")
    env_level = os.getenv("LOG_LEVEL")

    final_host = host or cfg_host or env_host or default_host
    final_port = int(port or cfg_port or (env_port or default_port))
    final_level = str(cfg_level or env_level or default_level).lower()

    return str(final_host), int(final_port), final_level


def _server_run():
    assert _server is not None
    try:
        _server.run()
    except Exception:
        _LOGGER.exception("uvicorn_run_failed")


def start_api_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
) -> None:
    """
    Запустить FastAPI + uvicorn в фоновом потоке.
    Повторный вызов — no-op, если сервер уже жив.
    """
    global _app, _server, _thread, _started

    with _lock:
        if _started and _server is not None and _thread is not None and _thread.is_alive():
            _LOGGER.debug("api_already_running")
            return

        # резолвим параметры
        rh, rp, rl = _resolve_host_port(host, port)
        if log_level:
            rl = str(log_level).lower()

        _app = _build_app()
        config = uvicorn.Config(
            _app,
            host=rh,
            port=rp,
            log_level=rl,
            lifespan="on",
            workers=1,
        )
        _server = uvicorn.Server(config)

        _thread = threading.Thread(target=_server_run, name="api-server", daemon=True)
        _thread.start()
        _started = True
        _LOGGER.info("api_starting", host=rh, port=rp, level=rl)

    # Короткое ожидание готовности (если uvicorn экспонирует флаг).
    # Не считаем ошибкой, если флаг недоступен — просто выходим.
    try:
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if getattr(_server, "started", False):  # type: ignore[attr-defined]
                _LOGGER.info("api_started")
                break
            if _thread is not None and not _thread.is_alive():
                _LOGGER.error("api_thread_terminated_early")
                break
            time.sleep(0.05)
    except Exception:
        pass


def stop_api_server(join: bool = False, timeout: Optional[float] = 5.0) -> None:
    """Остановить сервер (graceful)."""
    global _server, _thread, _started
    with _lock:
        srv = _server
        th = _thread
        if not _started or srv is None:
            return
        _LOGGER.info("api_stopping")
        srv.should_exit = True

    if join and th is not None:
        th.join(timeout=timeout)
    with _lock:
        _started = False
        _LOGGER.info("api_stopped")


def is_running() -> bool:
    with _lock:
        return bool(_started and _thread is not None and _thread.is_alive())


def get_application() -> FastAPI:
    """Вернуть инстанс FastAPI (создаст новый, если ещё не создан)."""
    global _app
    with _lock:
        if _app is None:
            _app = _build_app()
        return _app


__all__ = [
    "register_extension",
    "start_api_server",
    "stop_api_server",
    "is_running",
    "get_application",
]
