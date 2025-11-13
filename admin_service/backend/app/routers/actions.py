"""Administrative action endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import (
    ban_user,
    change_subscription_node,
    get_entity,
    issue_promocode,
    resume_subscription,
    suspend_subscription,
)
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import Node, Subscription, User
from ..schemas import (
    BanUserRequest,
    ChangeNodeRequest,
    IssuePromoCodeRequest,
    PromoCodeRead,
    ResumeSubscriptionRequest,
    SubscriptionRead,
    SuspendSubscriptionRequest,
    UserRead,
)

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/subscriptions/suspend", response_model=SubscriptionRead)
async def suspend_subscription_endpoint(
    data: SuspendSubscriptionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> SubscriptionRead:
    subscription = await get_entity(session, Subscription, data.subscription_id)
    subscription = await suspend_subscription(
        session,
        subscription,
        actor_user_id=current_user.id,
        ip_address=ip,
        reason=data.reason,
    )
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.post("/subscriptions/resume", response_model=SubscriptionRead)
async def resume_subscription_endpoint(
    data: ResumeSubscriptionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> SubscriptionRead:
    subscription = await get_entity(session, Subscription, data.subscription_id)
    subscription = await resume_subscription(
        session,
        subscription,
        actor_user_id=current_user.id,
        ip_address=ip,
        note=data.note,
    )
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.post("/promocodes/issue", response_model=PromoCodeRead)
async def issue_promocode_endpoint(
    data: IssuePromoCodeRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> PromoCodeRead:
    user = await get_entity(session, User, data.user_id)
    promocode = await issue_promocode(
        session,
        user=user,
        actor_user_id=current_user.id,
        ip_address=ip,
        code=data.code,
        discount_percent=data.discount_percent,
        valid_for_hours=data.valid_for_hours,
    )
    await session.commit()
    await session.refresh(promocode)
    return PromoCodeRead.model_validate(promocode)


@router.post("/subscriptions/change-node", response_model=SubscriptionRead)
async def change_subscription_node_endpoint(
    data: ChangeNodeRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> SubscriptionRead:
    subscription = await get_entity(session, Subscription, data.subscription_id)
    node = await get_entity(session, Node, data.node_id)
    subscription = await change_subscription_node(
        session,
        subscription=subscription,
        node=node,
        actor_user_id=current_user.id,
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.post("/users/ban", response_model=UserRead)
async def ban_user_endpoint(
    data: BanUserRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> UserRead:
    user = await get_entity(session, User, data.user_id)
    user = await ban_user(
        session,
        user=user,
        reason=data.reason,
        actor_user_id=current_user.id,
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)
