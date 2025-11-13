"""Audit log endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_active_user, get_db_session
from ..models import AuditLog, User
from ..schemas import AuditLogRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=list[AuditLogRead])
async def list_audit_logs(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    limit: int = 100,
) -> list[AuditLogRead]:
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [AuditLogRead.model_validate(log) for log in logs]
