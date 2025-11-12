from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class NodeType(str, enum.Enum):
    WIREGUARD = "wireguard"
    OPENVPN = "openvpn"
    AMNEZIA = "amnezia"


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    type = Column(Enum(NodeType), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    public_key = Column(String(255))
    settings = Column(JSON, default=dict)
    country = Column(String(64))
    city = Column(String(64))
    max_devices = Column(Integer, nullable=False, default=128)
    device_limit_per_user = Column(Integer, nullable=False, default=3)
    is_active = Column(Boolean, nullable=False, default=True)
    current_devices = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    key_pool = relationship("KeyPool", back_populates="node", cascade="all, delete-orphan")
    provisions = relationship("Provision", back_populates="node", cascade="all, delete-orphan")


class KeyPool(Base):
    __tablename__ = "key_pools"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    public_key = Column(String(255))
    private_key = Column(String(255))
    preshared_key = Column(String(255))
    certificate = Column(Text)
    ca_certificate = Column(Text)
    allocated = Column(Boolean, nullable=False, default=False)
    allocated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    node = relationship("Node", back_populates="key_pool")
    provision = relationship("Provision", back_populates="key", uselist=False)


class ProvisionStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class Provision(Base):
    __tablename__ = "provisions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    key_id = Column(Integer, ForeignKey("key_pools.id"))
    status = Column(Enum(ProvisionStatus), nullable=False, default=ProvisionStatus.ACTIVE)
    device_label = Column(String(128))
    file_name = Column(String(128))
    config_s3_key = Column(String(255))
    qr_s3_key = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime)

    node = relationship("Node", back_populates="provisions")
    key = relationship("KeyPool", back_populates="provision")
    peer = relationship("ActivePeer", back_populates="provision", uselist=False)


class ActivePeer(Base):
    __tablename__ = "active_peers"

    id = Column(Integer, primary_key=True)
    provision_id = Column(Integer, ForeignKey("provisions.id"), unique=True, nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    latest_handshake = Column(DateTime, default=datetime.utcnow)
    rx_bytes = Column(BigInteger, default=0)
    tx_bytes = Column(BigInteger, default=0)

    provision = relationship("Provision", back_populates="peer")

