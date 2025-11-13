"""Promo code management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit_event
from ..crud import create_promocode, delete_entity, get_entity, list_entities, update_promocode
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import PromoCode, User
from ..schemas import PromoCodeCreate, PromoCodeRead, PromoCodeUpdate

router = APIRouter(prefix="/promocodes", tags=["promocodes"])


@router.get("/", response_model=list[PromoCodeRead])
async def list_promocodes(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[PromoCodeRead]:
    promocodes = await list_entities(session, PromoCode, offset=offset, limit=limit)
    return [PromoCodeRead.model_validate(promocode) for promocode in promocodes]


@router.post("/", response_model=PromoCodeRead, status_code=201)
async def create_promocode_endpoint(
    data: PromoCodeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> PromoCodeRead:
    promocode = await create_promocode(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="promocode_create",
        target_type="promocode",
        target_id=str(promocode.id),
        metadata=data.model_dump(),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(promocode)
    return PromoCodeRead.model_validate(promocode)


@router.get("/{promocode_id}", response_model=PromoCodeRead)
async def get_promocode_endpoint(
    promocode_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> PromoCodeRead:
    promocode = await get_entity(session, PromoCode, promocode_id)
    return PromoCodeRead.model_validate(promocode)


@router.put("/{promocode_id}", response_model=PromoCodeRead)
async def update_promocode_endpoint(
    promocode_id: int,
    data: PromoCodeUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> PromoCodeRead:
    promocode = await get_entity(session, PromoCode, promocode_id)
    promocode = await update_promocode(session, promocode, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="promocode_update",
        target_type="promocode",
        target_id=str(promocode.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(promocode)
    return PromoCodeRead.model_validate(promocode)


@router.delete("/{promocode_id}", status_code=204)
async def delete_promocode_endpoint(
    promocode_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    promocode = await get_entity(session, PromoCode, promocode_id)
    await delete_entity(session, PromoCode, promocode_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="promocode_delete",
        target_type="promocode",
        target_id=str(promocode_id),
        metadata={"code": promocode.code},
        ip_address=ip,
    )
    await session.commit()
