"""Application configuration via environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AutoCase Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    data_dir: str = "./data"

    # Database
    database_url: str = "sqlite:///./data/autocase.db"

    # JWT
    secret_key: str = Field(default="change-me-please-change-me-please-32chars")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12h
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7d

    # Initial admin (created on first run if no users exist)
    initial_admin_username: str = "admin"
    initial_admin_password: str = "admin123"
    initial_admin_email: str = "admin@autocase.example"

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
