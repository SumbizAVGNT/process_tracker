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
    app_secret_key: str  # для подписей/сессий
    crypt_fernet_key: str  # Fernet.generate_key().decode()

    # --- Database ---
    db_url: str = "sqlite+aiosqlite:///./process_tracker.db"  # SQLAlchemy async URL

    # --- API Server ---
    api_host: str = "127.0.0.1"  # можно переопределить через ENV API_HOST
    api_port: int = 8787         # ENV API_PORT

    # --- CORS (через CSV в ENV CORS_ORIGINS) ---
    cors_origins: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # переменные из .env не чувствительны к регистру
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

    # Удобные флаги
    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"dev", "development"}

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


# Импортируемый singleton
settings = Settings()
