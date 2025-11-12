from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


class APIClientError(RuntimeError):
    pass


@dataclass(slots=True)
class TrialInfo:
    activated: bool
    expires_at: Optional[str]
    message: str


@dataclass(slots=True)
class SubscriptionStatus:
    status: str
    expires_at: Optional[str]
    plan: Optional[str]
    is_trial: bool


@dataclass(slots=True)
class ProvisionBundle:
    file_name: str
    file_bytes: bytes
    qr_bytes: Optional[bytes]


class BillingAPI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def start_trial(self, user_id: int) -> TrialInfo:
        payload = {"telegram_id": user_id}
        data = await self._request("POST", "/trial/start", json=payload)
        return TrialInfo(
            activated=data.get("activated", False),
            expires_at=data.get("expires_at"),
            message=data.get("message", "Trial выдан"),
        )

    async def subscription_status(self, user_id: int) -> SubscriptionStatus:
        params = {"telegram_id": user_id}
        data = await self._request("GET", "/subs/status", params=params)
        return SubscriptionStatus(
            status=data.get("status", "inactive"),
            expires_at=data.get("expires_at"),
            plan=data.get("plan"),
            is_trial=data.get("is_trial", False),
        )

    async def confirm_stars_payment(self, user_id: int, stars_tx_id: str, payload: str) -> None:
        body = {
            "telegram_id": user_id,
            "stars_tx_id": stars_tx_id,
            "payload": payload,
        }
        await self._request("POST", "/payments/confirm", json=body)


class ProvisionerAPI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def provision(self, user_id: int, node: Optional[str] = None) -> ProvisionBundle:
        payload: Dict[str, Any] = {"telegram_id": user_id}
        if node:
            payload["node"] = node
        data = await self._request("POST", "/provision", json=payload)
        file_name = data.get("file_name", "config.conf")
        file_content = data.get("file_content_base64")
        qr_base64 = data.get("qr_base64")
        if not file_content:
            raise APIClientError("Provisioner вернул пустой файл")
        file_bytes = base64.b64decode(file_content)
        qr_bytes = base64.b64decode(qr_base64) if qr_base64 else None
        return ProvisionBundle(file_name=file_name, file_bytes=file_bytes, qr_bytes=qr_bytes)
