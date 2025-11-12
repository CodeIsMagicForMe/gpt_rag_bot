from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Tuple

import segno

try:
    import wgctrl
except ImportError:  # pragma: no cover - optional dependency
    wgctrl = None

from db.models import KeyPool, Node, NodeType

logger = logging.getLogger(__name__)


class VPNManagerError(RuntimeError):
    pass


class BaseVPNManager:
    def generate_config(self, node: Node, key: KeyPool | None, *, device_label: str | None) -> Tuple[str, str]:
        raise NotImplementedError

    def revoke(self, node: Node, key: KeyPool | None) -> None:
        raise NotImplementedError


class WireGuardManager(BaseVPNManager):
    def __init__(self) -> None:
        self.client = wgctrl.WGCtrl() if wgctrl else None

    def generate_config(self, node: Node, key: KeyPool | None, *, device_label: str | None) -> Tuple[str, str]:
        if key is None:
            raise VPNManagerError("WireGuard key required")
        template = (
            "[Interface]\n"
            f"PrivateKey = {key.private_key}\n"
            "Address = 10.0.0.2/32\n"
            "DNS = 1.1.1.1\n\n"
            "[Peer]\n"
            f"PublicKey = {node.public_key}\n"
            f"PresharedKey = {key.preshared_key}\n"
            f"Endpoint = {node.endpoint}\n"
            "AllowedIPs = 0.0.0.0/0, ::/0\n"
        )
        file_name = f"{node.name}-{device_label or 'device'}.conf"
        if self.client and node.settings:
            interface_name = node.settings.get("interface")
            if interface_name:
                try:
                    self.client.configure_device(
                        interface_name,
                        private_key=None,
                        listen_port=None,
                        peers=[
                            {
                                "public_key": key.public_key,
                                "preshared_key": key.preshared_key,
                                "allowed_ips": "10.0.0.2/32",
                            }
                        ],
                    )
                except Exception:  # pragma: no cover - depends on host OS
                    logger.warning("Failed to push configuration via wgctrl", exc_info=True)
        return file_name, template

    def revoke(self, node: Node, key: KeyPool | None) -> None:
        if not key or not self.client or not node.settings:
            return
        interface_name = node.settings.get("interface")
        if not interface_name:
            return
        try:  # pragma: no cover - platform specific
            self.client.configure_device(interface_name, peers=[{"public_key": key.public_key, "remove": True}])
        except Exception:
            logger.warning("Failed to remove peer via wgctrl", exc_info=True)


class OpenVPNManager(BaseVPNManager):
    def __init__(self) -> None:
        self.easyrsa_path = os.getenv("EASYRSA", "/etc/openvpn/easy-rsa")

    def generate_config(self, node: Node, key: KeyPool | None, *, device_label: str | None) -> Tuple[str, str]:
        if key is None or not key.certificate:
            raise VPNManagerError("OpenVPN certificate is missing")
        template = (
            "client\nproto udp\nremote {endpoint}\n"
            "dev tun\nresolv-retry infinite\n"
            "nobind\npersist-key\npersist-tun\n"
            "cipher AES-256-GCM\nverb 3\n"
            "<ca>\n{ca}\n</ca>\n"
            "<cert>\n{cert}\n</cert>\n"
            "<key>\n{key}\n</key>\n"
        ).format(endpoint=node.endpoint, ca=key.ca_certificate or "", cert=key.certificate, key=key.private_key)
        file_name = f"{node.name}-{device_label or 'device'}.ovpn"
        return file_name, template

    def revoke(self, node: Node, key: KeyPool | None) -> None:
        if not key:
            return
        cert_name = key.public_key or key.private_key
        if not cert_name:
            return
        index_txt = Path(self.easyrsa_path) / "pki" / "index.txt"
        if not index_txt.exists():
            return
        revoke_cmd = ["easyrsa", "revoke", cert_name]
        try:
            subprocess.run(revoke_cmd, check=False, capture_output=True)
        except FileNotFoundError:  # pragma: no cover - env specific
            logger.warning("easy-rsa binary not found for revoke")


class AmneziaManager(BaseVPNManager):
    def __init__(self, cli_path: str) -> None:
        self.cli_path = cli_path

    def generate_config(self, node: Node, key: KeyPool | None, *, device_label: str | None) -> Tuple[str, str]:
        args = [self.cli_path, "profile", "export", "--node", node.name]
        if device_label:
            args.extend(["--label", device_label])
        try:
            result = subprocess.run(args, capture_output=True, check=True, text=True)
            payload = result.stdout
        except FileNotFoundError:  # pragma: no cover
            payload = f"amnezia://{node.endpoint}/{device_label or 'device'}"
        except subprocess.CalledProcessError as exc:  # pragma: no cover
            raise VPNManagerError("Amnezia CLI failed") from exc
        file_name = f"{node.name}-{device_label or 'device'}.amnezia"
        return file_name, payload

    def revoke(self, node: Node, key: KeyPool | None) -> None:
        args = [self.cli_path, "profile", "revoke", "--node", node.name]
        if key and key.public_key:
            args.extend(["--key", key.public_key])
        try:
            subprocess.run(args, check=False, capture_output=True)
        except FileNotFoundError:  # pragma: no cover
            logger.warning("Amnezia CLI not found for revoke")


def build_qr_bytes(payload: str, *, error_correction: str) -> bytes:
    qr = segno.make(payload, error=error_correction)
    from io import BytesIO

    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=4)
    return buffer.getvalue()


def get_vpn_manager(node_type: NodeType, *, amnezia_cli_path: str) -> BaseVPNManager:
    managers: Dict[NodeType, BaseVPNManager] = {
        NodeType.WIREGUARD: WireGuardManager(),
        NodeType.OPENVPN: OpenVPNManager(),
        NodeType.AMNEZIA: AmneziaManager(amnezia_cli_path),
    }
    return managers[node_type]
