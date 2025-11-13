"""Configuration helpers for the admin backend service."""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration for the admin backend."""

    app_name: str = "Admin Backend"
    secret_key: str = Field(..., description="JWT secret key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = Field(
        "sqlite+aiosqlite:///./admin.db", description="SQLAlchemy database URL"
    )
    allowed_ips: List[str] = Field(
        default_factory=lambda: ["127.0.0.1", "::1"],
        description="List of IP addresses allowed to access the API",
    )
    bootstrap_admin_email: Optional[str] = Field(
        default=None, description="Email for bootstrap admin user"
    )
    bootstrap_admin_password: Optional[str] = Field(
        default=None, description="Password for bootstrap admin user"
    )

    class Config:
        env_prefix = "ADMIN_SERVICE_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
