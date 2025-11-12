from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class ProvisionerSettings(BaseSettings):
    database_url: str = Field("sqlite:///./provisioner.db", alias="DATABASE_URL")
    max_devices_per_user: int = Field(3, alias="MAX_DEVICES_PER_USER", ge=1)
    s3_bucket: str = Field("local-bucket", alias="S3_BUCKET")
    s3_access_key: str = Field("local", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field("local", alias="S3_SECRET_KEY")
    s3_region: str = Field("us-east-1", alias="S3_REGION")
    s3_endpoint_url: Optional[str] = Field(None, alias="S3_ENDPOINT_URL")
    s3_presign_ttl: int = Field(900, alias="S3_PRESIGN_TTL", ge=60)
    statsd_host: str = Field("localhost", alias="STATSD_HOST")
    statsd_port: int = Field(8125, alias="STATSD_PORT")
    statsd_prefix: str = Field("provisioner", alias="STATSD_PREFIX")
    qr_error_correction: str = Field("M", alias="QR_ERROR_CORRECTION")
    amnezia_cli_path: str = Field("amnezia", alias="AMNEZIA_CLI_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> ProvisionerSettings:
    return ProvisionerSettings()  # type: ignore[arg-type]
