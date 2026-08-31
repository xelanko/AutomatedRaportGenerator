"""
Typed API settings via pydantic-settings — separate from the pipeline's
own config.py. Every field is overridable through env vars (prefixed
REPORT_API_) or a .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REPORT_API_", env_file=".env", extra="ignore")

    api_key: str = "dev-local-key"       # required in X-API-Key header on protected routes
    cors_origins: list[str] = ["*"]
    rate_limit_per_minute: int = 60
    max_upload_mb: int = 10


@lru_cache
def get_settings() -> APISettings:
    return APISettings()