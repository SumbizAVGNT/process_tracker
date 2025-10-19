from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog

from .config import settings


def setup_logging() -> None:
    """
    Инициализация логирования:
    - базовый уровень из .env (LOG_LEVEL)
    - JSON-логи через structlog
    - увязываем уровни uvicorn/fastapi
    """
    if getattr(setup_logging, "_configured", False):
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # stdlib -> stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    logging.basicConfig(
        level=level,
        handlers=[handler],
        # оставляем формат пустым — structlog сам отрисует JSON
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="ISO", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # выравниваем уровень для веб-сервера
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(level)

    # полезный контекст по умолчанию
    bind_context(app="process-tracker", env=settings.app_env)

    setup_logging._configured = True


def get_logger(name: Optional[str] = None) -> "structlog.stdlib.BoundLogger":
    return structlog.get_logger(name) if name else structlog.get_logger()


def bind_context(**kwargs) -> None:
    """Привязать контекст (запишется во все последующие логи этого потока/таска)."""
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Удалить ключи из контекста."""
    if keys:
        structlog.contextvars.unbind_contextvars(*keys)


# Глобальный логгер «по умолчанию»
logger = get_logger("process-tracker")
