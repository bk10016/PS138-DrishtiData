from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    app_version: str = "0.1.0"
    model_version: str = "hybrid-synthetic-0.1"  # ASSUMPTION: bump when artifacts are retrained
    data_dir: Path = BACKEND_ROOT / "data"
    # Swapping to PostgreSQL is a URL change only: postgresql+psycopg://user:pw@host/db
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'data' / 'qgreen.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
