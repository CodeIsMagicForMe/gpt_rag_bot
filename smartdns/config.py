from __future__ import annotations

from functools import lru_cache
from ipaddress import ip_address
from typing import List

from pydantic import BaseSettings, Field, field_validator


class SmartDNSSettings(BaseSettings):
    host: str = Field("0.0.0.0", alias="SMARTDNS_HOST")
    port: int = Field(1053, alias="SMARTDNS_PORT")
    enable_tcp: bool = Field(True, alias="SMARTDNS_ENABLE_TCP")
    reload_interval: int = Field(30, alias="SMARTDNS_RELOAD_INTERVAL")
    rules_backend: str = Field("auto", alias="SMARTDNS_RULES_BACKEND")
    rules_file: str | None = Field(None, alias="SMARTDNS_RULES_FILE")
    database_url: str = Field("sqlite:///./provisioner.db", alias="DATABASE_URL")
    upstream_servers: List[str] = Field(
        default_factory=lambda: ["1.1.1.1:53", "8.8.8.8:53"],
        alias="SMARTDNS_UPSTREAMS",
    )
    upstream_timeout: float = Field(2.0, alias="SMARTDNS_UPSTREAM_TIMEOUT")
    metrics_host: str = Field("0.0.0.0", alias="SMARTDNS_METRICS_HOST")
    metrics_port: int = Field(9105, alias="SMARTDNS_METRICS_PORT")
    monitor_domain: str = Field("example.com", alias="SMARTDNS_MONITOR_DOMAIN")
    monitor_interval: int = Field(30, alias="SMARTDNS_MONITOR_INTERVAL")
    monitor_timeout: float = Field(2.0, alias="SMARTDNS_MONITOR_TIMEOUT")
    monitor_host: str = Field("127.0.0.1", alias="SMARTDNS_MONITOR_HOST")
    monitor_port: int = Field(1053, alias="SMARTDNS_MONITOR_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("upstream_servers", mode="before")
    @classmethod
    def _split_upstreams(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("monitor_domain")
    @classmethod
    def _normalize_domain(cls, value: str) -> str:
        return value.rstrip(".").lower()

    @field_validator("rules_backend")
    @classmethod
    def _validate_backend(cls, value: str) -> str:
        allowed = {"auto", "db", "file", "both"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"rules_backend must be one of {allowed}")
        return normalized

    @field_validator("host", "metrics_host", "monitor_host", mode="before")
    @classmethod
    def _validate_host(cls, value: str) -> str:
        if value:
            ip_address(value)  # raises ValueError for invalid hosts
        return value


@lru_cache(maxsize=1)
def get_settings() -> SmartDNSSettings:
    return SmartDNSSettings()  # type: ignore[arg-type]
