"""Application settings, loaded once from environment variables (12-factor)."""

from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_APP_NOW = datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)
_DEV_SECRET = "dev-insecure-change-me"
_BACKEND_ROOT = Path(__file__).resolve().parents[2]  # src/config/settings.py -> backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    app_name: str = "L10 Meeting API"
    environment: Literal["local", "test", "production"] = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://l10:l10@localhost:5432/l10"
    db_pool_size: int = 10
    db_echo: bool = False

    # "Now" for the whole app. Nothing reads the system clock directly.
    app_now: datetime = DEFAULT_APP_NOW
    app_clock_mode: Literal["running", "frozen"] = "running"

    session_secret: str = _DEV_SECRET
    session_cookie_name: str = "l10_session"
    session_max_age_s: int = 60 * 60 * 12
    cookie_secure: bool = False

    cors_origins: list[str] = Field(default_factory=list)
    seed_path: Path = _BACKEND_ROOT / "seed" / "seed.json"

    @field_validator("app_now")
    @classmethod
    def _app_now_is_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("APP_NOW must include a UTC offset, e.g. 2026-11-11T15:00:00Z")
        return v.astimezone(UTC)

    @model_validator(mode="after")
    def _no_dev_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.session_secret == _DEV_SECRET:
            raise ValueError("SESSION_SECRET must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
