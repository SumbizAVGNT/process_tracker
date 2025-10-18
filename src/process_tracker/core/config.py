# src/process_tracker/core/config.py
from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # --- App / Env ---
    app_env: str = "dev"  # dev | prod | test
    log_level: str = "INFO"

    # --- Secrets / Crypto ---
    app_secret_key: str
    crypt_fernet_key: str  # Fernet.generate_key().decode()

    # --- Database (SQLAlchemy async URL) ---
    db_url: str = "sqlite+aiosqlite:///./process_tracker.db"

    # Пул и таймауты (для не-SQLite будут применены полностью)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800  # сек
    db_query_timeout: float = 5.0  # сек, asyncio timeout на запрос
    db_max_concurrency: int = 20  # ограничение параллельных запросов в БД

    # --- API Server ---
    api_host: str = "127.0.0.1"
    api_port: int = 8787

    # --- CORS (через CSV в ENV CORS_ORIGINS) ---
    cors_origins: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
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


settings = Settings()
