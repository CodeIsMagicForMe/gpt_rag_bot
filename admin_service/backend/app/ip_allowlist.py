"""Middleware enforcing access based on IP allow lists."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import get_settings


class IPAllowListMiddleware(BaseHTTPMiddleware):
    """Reject requests originating from IPs outside the configured allow list."""

    def __init__(self, app, allowed_ips: Iterable[str] | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.allowed_ips = {ip_address(ip) for ip in (allowed_ips or settings.allowed_ips)}

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        client_host = request.client.host if request.client else None
        if client_host is None:
            return JSONResponse({"detail": "Unable to determine client IP"}, status_code=403)

        try:
            client_ip = ip_address(client_host)
        except ValueError:
            return JSONResponse({"detail": "Invalid client IP"}, status_code=403)

        if client_ip not in self.allowed_ips:
            return JSONResponse({"detail": "IP address not allowed"}, status_code=403)

        return await call_next(request)
