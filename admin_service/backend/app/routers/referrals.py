"""Referral management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit_event
from ..crud import create_referral, delete_entity, get_entity, list_entities, update_referral
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import Referral, User
from ..schemas import ReferralCreate, ReferralRead, ReferralUpdate

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("/", response_model=list[ReferralRead])
async def list_referrals(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[ReferralRead]:
    referrals = await list_entities(session, Referral, offset=offset, limit=limit)
    return [ReferralRead.model_validate(referral) for referral in referrals]


@router.post("/", response_model=ReferralRead, status_code=201)
async def create_referral_endpoint(
    data: ReferralCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> ReferralRead:
    referral = await create_referral(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="referral_create",
        target_type="referral",
        target_id=str(referral.id),
        metadata=data.model_dump(),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(referral)
    return ReferralRead.model_validate(referral)


@router.get("/{referral_id}", response_model=ReferralRead)
async def get_referral_endpoint(
    referral_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> ReferralRead:
    referral = await get_entity(session, Referral, referral_id)
    return ReferralRead.model_validate(referral)


@router.put("/{referral_id}", response_model=ReferralRead)
async def update_referral_endpoint(
    referral_id: int,
    data: ReferralUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> ReferralRead:
    referral = await get_entity(session, Referral, referral_id)
    referral = await update_referral(session, referral, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="referral_update",
        target_type="referral",
        target_id=str(referral.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(referral)
    return ReferralRead.model_validate(referral)


@router.delete("/{referral_id}", status_code=204)
async def delete_referral_endpoint(
    referral_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    await get_entity(session, Referral, referral_id)
    await delete_entity(session, Referral, referral_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="referral_delete",
        target_type="referral",
        target_id=str(referral_id),
        metadata=None,
        ip_address=ip,
    )
    await session.commit()
