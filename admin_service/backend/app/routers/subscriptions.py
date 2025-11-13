"""Subscription management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit_event
from ..crud import (
    create_subscription,
    delete_entity,
    get_entity,
    list_entities,
    update_subscription,
)
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import Subscription, User
from ..schemas import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/", response_model=list[SubscriptionRead])
async def list_subscriptions(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[SubscriptionRead]:
    subscriptions = await list_entities(
        session, Subscription, offset=offset, limit=limit
    )
    return [SubscriptionRead.model_validate(item) for item in subscriptions]


@router.post("/", response_model=SubscriptionRead, status_code=201)
async def create_subscription_endpoint(
    data: SubscriptionCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> SubscriptionRead:
    subscription = await create_subscription(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="subscription_create",
        target_type="subscription",
        target_id=str(subscription.id),
        metadata=data.model_dump(),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription_endpoint(
    subscription_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> SubscriptionRead:
    subscription = await get_entity(session, Subscription, subscription_id)
    return SubscriptionRead.model_validate(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription_endpoint(
    subscription_id: int,
    data: SubscriptionUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> SubscriptionRead:
    subscription = await get_entity(session, Subscription, subscription_id)
    subscription = await update_subscription(session, subscription, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="subscription_update",
        target_type="subscription",
        target_id=str(subscription.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=204)
async def delete_subscription_endpoint(
    subscription_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    await get_entity(session, Subscription, subscription_id)
    await delete_entity(session, Subscription, subscription_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="subscription_delete",
        target_type="subscription",
        target_id=str(subscription_id),
        ip_address=ip,
        metadata=None,
    )
    await session.commit()
