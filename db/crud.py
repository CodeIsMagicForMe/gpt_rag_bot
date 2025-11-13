from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from .models import ActivePeer, KeyPool, Node, Provision, ProvisionStatus


class KeyPoolEmpty(RuntimeError):
    pass


def get_node(session: Session, node_id: Optional[int] = None) -> Node:
    query = select(Node).where(Node.is_active.is_(True))
    if node_id is not None:
        query = query.where(Node.id == node_id)
    else:
        query = query.where(Node.current_devices < Node.max_devices)
    query = query.order_by(Node.current_devices.asc())
    result = session.execute(query).scalars().first()
    if not result:
        raise NoResultFound("Node not found or not active")
    return result


def count_user_devices(session: Session, telegram_id: int) -> int:
    query = select(func.count(Provision.id)).where(
        Provision.telegram_id == telegram_id,
        Provision.status == ProvisionStatus.ACTIVE,
    )
    return session.execute(query).scalar_one()


def count_user_devices_on_node(session: Session, telegram_id: int, node_id: int) -> int:
    query = select(func.count(Provision.id)).where(
        Provision.telegram_id == telegram_id,
        Provision.node_id == node_id,
        Provision.status == ProvisionStatus.ACTIVE,
    )
    return session.execute(query).scalar_one()


def allocate_key(session: Session, node_id: int) -> KeyPool:
    query = (
        select(KeyPool)
        .where(KeyPool.node_id == node_id, KeyPool.allocated.is_(False))
        .order_by(KeyPool.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    key = session.execute(query).scalars().first()
    if not key:
        raise KeyPoolEmpty("Key pool is empty")
    key.allocated = True
    key.allocated_at = datetime.utcnow()
    session.add(key)
    return key


def release_key(session: Session, key_id: int) -> None:
    key = session.get(KeyPool, key_id)
    if key:
        key.allocated = False
        key.allocated_at = None
        session.add(key)


def create_provision(
    session: Session,
    *,
    telegram_id: int,
    node: Node,
    key: Optional[KeyPool],
    file_name: str,
    config_s3_key: str,
    qr_s3_key: Optional[str],
    device_label: Optional[str],
) -> Provision:
    provision = Provision(
        telegram_id=telegram_id,
        node=node,
        key=key,
        file_name=file_name,
        config_s3_key=config_s3_key,
        qr_s3_key=qr_s3_key,
        device_label=device_label,
    )
    session.add(provision)
    node.current_devices += 1
    session.add(node)
    session.flush()
    peer = ActivePeer(provision_id=provision.id, node_id=node.id)
    session.add(peer)
    return provision


def revoke_provision(session: Session, provision: Provision) -> Provision:
    if provision.status is ProvisionStatus.REVOKED:
        return provision
    provision.status = ProvisionStatus.REVOKED
    provision.revoked_at = datetime.utcnow()
    session.add(provision)
    node = provision.node
    if node.current_devices > 0:
        node.current_devices -= 1
        session.add(node)
    if provision.key_id:
        release_key(session, provision.key_id)
    if provision.peer:
        session.delete(provision.peer)
    return provision


def get_active_provision(session: Session, telegram_id: int, provision_id: int) -> Provision:
    provision = session.get(Provision, provision_id)
    if not provision or provision.telegram_id != telegram_id:
        raise NoResultFound("Provision not found")
    if provision.status is not ProvisionStatus.ACTIVE:
        raise NoResultFound("Provision is revoked")
    return provision


def update_peer_stats(
    session: Session,
    provision_id: int,
    *,
    rx_bytes: int,
    tx_bytes: int,
    latest_handshake: datetime,
) -> None:
    peer = session.execute(
        select(ActivePeer).where(ActivePeer.provision_id == provision_id)
    ).scalars().first()
    if peer is None:
        provision = session.get(Provision, provision_id)
        if provision is None:
            return
        peer = ActivePeer(provision_id=provision_id, node_id=provision.node_id)
    peer.rx_bytes = rx_bytes
    peer.tx_bytes = tx_bytes
    peer.latest_handshake = latest_handshake
    session.add(peer)


def list_active_nodes(session: Session) -> List[Node]:
    return session.execute(select(Node).where(Node.is_active.is_(True))).scalars().all()
