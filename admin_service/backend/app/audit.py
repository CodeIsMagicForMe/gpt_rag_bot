"""Utilities for recording audit log events."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog


async def record_audit_event(
    session: AsyncSession,
    *,
    actor_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: str,
    metadata: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata,
        ip_address=ip_address,
    )
    session.add(event)
    await session.flush()
    return event
