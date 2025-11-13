from __future__ import annotations

import base64
import logging
import uuid
from typing import Callable

from statsd import StatsClient

from sqlalchemy.exc import NoResultFound

from db import ENGINE, Base
from db.crud import (
    KeyPoolEmpty,
    allocate_key,
    count_user_devices,
    count_user_devices_on_node,
    create_provision,
    get_active_provision,
    get_node,
    list_active_nodes,
    revoke_provision,
    update_peer_stats,
)
from db.models import Node, NodeType

from .config import ProvisionerSettings
from .metrics import PROVISION_ERRORS, PROVISION_REQUESTS, REVOCATION_REQUESTS, SWITCH_REQUESTS
from .s3 import S3Uploader
from .schemas import ActivePeerStats, ProvisionRequest, ProvisionResponse, SwitchNodeRequest
from .vpn import VPNManagerError, build_qr_bytes, get_vpn_manager

logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=ENGINE)


class ProvisioningError(RuntimeError):
    pass


class ProvisioningService:
    def __init__(
        self,
        *,
        session_factory: Callable,
        settings: ProvisionerSettings,
        s3_uploader: S3Uploader,
        statsd: StatsClient,
    ) -> None:
        self._session_factory = session_factory
        self.settings = settings
        self.s3 = s3_uploader
        self.statsd = statsd

    def provision(self, payload: ProvisionRequest) -> ProvisionResponse:
        with self._session_factory() as session:
            devices = count_user_devices(session, payload.telegram_id)
            if devices >= self.settings.max_devices_per_user:
                raise ProvisioningError("Device limit reached")
            node = self._pick_node(session, payload)
            if node.current_devices >= node.max_devices:
                raise ProvisioningError("Node capacity reached")
            per_node = count_user_devices_on_node(session, payload.telegram_id, node.id)
            if per_node >= node.device_limit_per_user:
                raise ProvisioningError("Node limit reached for user")
            key = None
            if node.type in {NodeType.WIREGUARD, NodeType.OPENVPN}:
                try:
                    key = allocate_key(session, node.id)
                except KeyPoolEmpty as exc:
                    raise ProvisioningError("Key pool depleted") from exc
            manager = get_vpn_manager(node.type, amnezia_cli_path=self.settings.amnezia_cli_path)
            try:
                file_name, config_text = manager.generate_config(node, key, device_label=payload.device_label)
            except VPNManagerError as exc:
                raise ProvisioningError(str(exc)) from exc
            qr_bytes = build_qr_bytes(config_text, error_correction=self.settings.qr_error_correction)
            config_bytes = config_text.encode()
            config_s3_key = f"configs/{uuid.uuid4()}.conf"
            qr_s3_key = f"qrs/{uuid.uuid4()}.png"
            self.s3.upload_bytes(config_s3_key, config_bytes, content_type="text/plain")
            self.s3.upload_bytes(qr_s3_key, qr_bytes, content_type="image/png")
            provision = create_provision(
                session,
                telegram_id=payload.telegram_id,
                node=node,
                key=key,
                file_name=file_name,
                config_s3_key=config_s3_key,
                qr_s3_key=qr_s3_key,
                device_label=payload.device_label,
            )
            session.commit()
            PROVISION_REQUESTS.inc()
            self.statsd.incr("provision.success")
            return ProvisionResponse(
                provision_id=provision.id,
                node_id=node.id,
                node_name=node.name,
                file_name=file_name,
                file_content_base64=base64.b64encode(config_bytes).decode(),
                qr_base64=base64.b64encode(qr_bytes).decode(),
                file_url=self.s3.generate_presigned_url(config_s3_key),
                qr_url=self.s3.generate_presigned_url(qr_s3_key),
            )

    def revoke(self, telegram_id: int, provision_id: int) -> None:
        with self._session_factory() as session:
            try:
                provision = get_active_provision(session, telegram_id, provision_id)
            except NoResultFound as exc:
                raise ProvisioningError("Device not found") from exc
            manager = get_vpn_manager(
                provision.node.type,
                amnezia_cli_path=self.settings.amnezia_cli_path,
            )
            manager.revoke(provision.node, provision.key)
            revoke_provision(session, provision)
            session.commit()
            REVOCATION_REQUESTS.inc()
            self.statsd.incr("provision.revoke")

    def switch_node(self, request: SwitchNodeRequest) -> ProvisionResponse:
        with self._session_factory() as session:
            try:
                provision = get_active_provision(session, request.telegram_id, request.device_id)
            except NoResultFound as exc:
                raise ProvisioningError("Device not found") from exc
            device_label = provision.device_label
            revoke_provision(session, provision)
            session.commit()
        REVOCATION_REQUESTS.inc()
        self.statsd.incr("provision.switch_revoke")
        SWITCH_REQUESTS.inc()
        new_request = ProvisionRequest(
            telegram_id=request.telegram_id,
            preferred_node=request.target_node,
            device_label=device_label,
        )
        return self.provision(new_request)

    def refresh_peer_stats(self, stats: list[ActivePeerStats]) -> None:
        with self._session_factory() as session:
            for peer in stats:
                update_peer_stats(
                    session,
                    peer.provision_id,
                    rx_bytes=peer.rx_bytes,
                    tx_bytes=peer.tx_bytes,
                    latest_handshake=peer.latest_handshake,
                )
            session.commit()

    def _pick_node(self, session, payload: ProvisionRequest) -> Node:
        try:
            if payload.preferred_node:
                return get_node(session, payload.preferred_node)
            return get_node(session)
        except NoResultFound as exc:
            raise ProvisioningError("No nodes available") from exc

    def list_nodes(self) -> list[dict]:
        with self._session_factory() as session:
            nodes = list_active_nodes(session)
            return [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "country": node.country,
                    "city": node.city,
                    "max_devices": node.max_devices,
                    "current_devices": node.current_devices,
                }
                for node in nodes
            ]
