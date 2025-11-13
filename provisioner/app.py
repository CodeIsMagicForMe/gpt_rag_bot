from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from statsd import StatsClient

from db import session_scope

from .config import ProvisionerSettings, get_settings

SETTINGS = get_settings()
os.environ.setdefault("DATABASE_URL", SETTINGS.database_url)

from .metrics import PROVISION_ERRORS
from .s3 import S3Uploader
from .schemas import (
    ProvisionRequest,
    ProvisionResponse,
    RevokeRequest,
    RevokeResponse,
    StatsUpdateRequest,
    SwitchNodeRequest,
)
from .service import ProvisioningError, ProvisioningService

logger = logging.getLogger(__name__)


def _build_service(settings: ProvisionerSettings) -> ProvisioningService:
    statsd_client = StatsClient(host=settings.statsd_host, port=settings.statsd_port, prefix=settings.statsd_prefix)
    s3_uploader = S3Uploader(
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        region=settings.s3_region,
        presign_ttl=settings.s3_presign_ttl,
        endpoint_url=settings.s3_endpoint_url,
        sse_algorithm=settings.s3_sse_algorithm,
        sse_kms_key_id=settings.s3_sse_kms_key_id,
    )
    return ProvisioningService(
        session_factory=session_scope,
        settings=settings,
        s3_uploader=s3_uploader,
        statsd=statsd_client,
    )


def create_app() -> FastAPI:
    service = _build_service(SETTINGS)
    app = FastAPI(title="Provisioner", version="1.0.0")

    @app.post("/provision", response_model=ProvisionResponse)
    async def provision_endpoint(request: ProvisionRequest) -> ProvisionResponse:
        try:
            return await run_in_threadpool(service.provision, request)
        except ProvisioningError as exc:
            PROVISION_ERRORS.inc()
            service.statsd.incr("provision.error")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            PROVISION_ERRORS.inc()
            service.statsd.incr("provision.error")
            logger.exception("Provision failed")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/revoke", response_model=RevokeResponse)
    async def revoke_endpoint(request: RevokeRequest) -> RevokeResponse:
        try:
            await run_in_threadpool(service.revoke, request.telegram_id, request.device_id)
            return RevokeResponse(device_id=request.device_id, status="revoked")
        except ProvisioningError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            logger.exception("Revoke failed")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/switch_node", response_model=ProvisionResponse)
    async def switch_node(request: SwitchNodeRequest) -> ProvisionResponse:
        try:
            return await run_in_threadpool(service.switch_node, request)
        except ProvisioningError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            logger.exception("Switch node failed")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/stats/peers")
    async def stats_endpoint(request: StatsUpdateRequest) -> JSONResponse:
        await run_in_threadpool(service.refresh_peer_stats, request.peers)
        return JSONResponse({"status": "ok"})

    @app.get("/nodes")
    async def list_nodes() -> JSONResponse:
        data = await run_in_threadpool(service.list_nodes)
        return JSONResponse(data)

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/healthz")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
