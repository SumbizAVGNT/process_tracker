from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Найти и подгрузить .env из КОРНЯ проекта независимо от CWD ---
# config.py -> core -> process_tracker -> src -> <PROJECT_ROOT>
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
try:
    from dotenv import load_dotenv  # type: ignore
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=False)
except Exception:
    # dotenv не обязателен — просто игнорируем, если не установлен
    pass


def _dev_secret() -> str:
    return secrets.token_urlsafe(48)


def _dev_fernet_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


class Settings(BaseSettings):
    # Общие
    app_name: str = "process-tracker"
    app_env: str = "dev"
    log_level: str = "INFO"

    # Secrets (дефолты для dev, чтобы не падать без .env)
    app_secret_key: str = Field(default_factory=_dev_secret)
    crypt_fernet_key: str = Field(default_factory=_dev_fernet_key)

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8787
    cors_origins: list[str] = Field(default_factory=list)

    # DB
    # относительный путь будет резолвиться к PROJECT_ROOT (см. db_url_resolved)
    db_url: str = "sqlite+aiosqlite:///./process_tracker.db"
    db_echo: bool = False
    db_query_timeout: float = 10.0
    db_max_concurrency: int = 8  # 🔹 ограничение параллельных запросов (для семафора)

    # Служебное
    project_root: Path = Field(default_factory=lambda: PROJECT_ROOT)

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @computed_field
    @property
    def db_url_resolved(self) -> str:
        """
        Если указан относительный SQLite URL вида sqlite+aiosqlite:///./file.db,
        превращаем его в абсолютный путь относительно project_root.
        """
        url = (self.db_url or "").strip()
        prefix = "sqlite+aiosqlite:///./"
        if url.startswith(prefix):
            rel = url[len(prefix):]
            abs_path = (self.project_root / rel).resolve()
            return f"sqlite+aiosqlite:///{abs_path.as_posix()}"
        return url


settings = Settings()
