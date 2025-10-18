# src/process_tracker/core/config.py
from __future__ import annotations

import secrets
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from dotenv import load_dotenv, find_dotenv

# Подхватываем .env из текущей папки или выше (по дереву)
load_dotenv(find_dotenv(usecwd=True), override=False)


class Settings(BaseSettings):
    # --- App / Env ---
    app_env: str = "dev"  # dev | prod | test
    log_level: str = "INFO"

    # --- Secrets / Crypto ---
    app_secret_key: Optional[str] = None            # для подписей/сессий
    crypt_fernet_key: Optional[str] = None          # Fernet.generate_key().decode()

    # --- Database (SQLAlchemy async URL) ---
    db_url: str = "sqlite+aiosqlite:///./process_tracker.db"

    # Пул и таймауты (для не-SQLite будут применены полностью)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800     # сек
    db_query_timeout: float = 5.0   # сек, asyncio timeout на запрос
    db_max_concurrency: int = 20    # ограничение параллельных запросов к БД

    # --- API Server ---
    api_host: str = "127.0.0.1"
    api_port: int = 8787

    # --- CORS (через CSV в ENV CORS_ORIGINS) ---
    cors_origins: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",                 # всё ещё поддерживаем локальный .env
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return (v or "INFO").upper()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            items = [s.strip() for s in v.split(",") if s.strip()]
            return items
        return v

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"dev", "development"}

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}

    # Генерируем ключи в DEV, требуем явно в PROD
    @model_validator(mode="after")
    def _ensure_keys(self):
        if not self.app_secret_key:
            if self.is_dev:
                # безопасный временный ключ (только для dev)
                self.app_secret_key = secrets.token_urlsafe(48)
            else:
                raise ValueError("APP_SECRET_KEY is required in production")

        if not self.crypt_fernet_key:
            if self.is_dev:
                # временный (DEV); для PROD сгенерируй Fernet.generate_key().decode()
                from cryptography.fernet import Fernet
                self.crypt_fernet_key = Fernet.generate_key().decode()
            else:
                raise ValueError("CRYPT_FERNET_KEY is required in production")

        return self


# Импортируемый singleton
settings = Settings()
