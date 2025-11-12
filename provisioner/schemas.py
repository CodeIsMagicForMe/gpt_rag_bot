from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProvisionRequest(BaseModel):
    telegram_id: int = Field(..., ge=1)
    preferred_node: Optional[int] = Field(None, description="Explicit node id")
    device_label: Optional[str] = Field(None, max_length=128)


class ProvisionResponse(BaseModel):
    provision_id: int
    node_id: int
    node_name: str
    file_name: str
    file_content_base64: str
    qr_base64: Optional[str]
    file_url: str
    qr_url: Optional[str]


class RevokeRequest(BaseModel):
    telegram_id: int = Field(..., ge=1)
    device_id: int = Field(..., ge=1)


class RevokeResponse(BaseModel):
    device_id: int
    status: str


class SwitchNodeRequest(BaseModel):
    telegram_id: int = Field(..., ge=1)
    device_id: int = Field(..., ge=1)
    target_node: Optional[int]


class ActivePeerStats(BaseModel):
    provision_id: int
    rx_bytes: int
    tx_bytes: int
    latest_handshake: datetime


class StatsUpdateRequest(BaseModel):
    peers: list[ActivePeerStats]
