"""CRUD helper functions for the admin service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .audit import record_audit_event
from .models import (
    Node,
    Plan,
    PromoCode,
    Referral,
    Subscription,
    User,
)
from .security import hash_password, verify_password


async def create_user(session: AsyncSession, data) -> User:
    hashed = hash_password(data.password)
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hashed,
        is_active=data.is_active,
        is_banned=data.is_banned,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - DB constraint
        raise HTTPException(status_code=400, detail="Email already exists") from exc
    return user


async def list_entities(session: AsyncSession, model, offset: int = 0, limit: int = 50):
    result = await session.execute(select(model).offset(offset).limit(limit))
    return result.scalars().all()


async def get_entity(session: AsyncSession, model, entity_id: int):
    result = await session.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return entity


async def update_user(session: AsyncSession, user: User, data) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_banned is not None:
        user.is_banned = data.is_banned
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    await session.flush()
    return user


async def delete_entity(session: AsyncSession, model, entity_id: int) -> None:
    entity = await get_entity(session, model, entity_id)
    await session.delete(entity)


async def create_plan(session: AsyncSession, data) -> Plan:
    plan = Plan(**data.model_dump())
    session.add(plan)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Plan name already exists") from exc
    return plan


async def update_plan(session: AsyncSession, plan: Plan, data) -> Plan:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await session.flush()
    return plan


async def create_node(session: AsyncSession, data) -> Node:
    node = Node(**data.model_dump())
    session.add(node)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Node name already exists") from exc
    return node


async def update_node(session: AsyncSession, node: Node, data) -> Node:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(node, field, value)
    await session.flush()
    return node


async def create_subscription(session: AsyncSession, data) -> Subscription:
    subscription = Subscription(**data.model_dump())
    session.add(subscription)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Invalid subscription reference") from exc
    return subscription


async def update_subscription(session: AsyncSession, subscription: Subscription, data) -> Subscription:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)
    await session.flush()
    return subscription


async def create_promocode(session: AsyncSession, data) -> PromoCode:
    promocode = PromoCode(**data.model_dump())
    session.add(promocode)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Promo code already exists") from exc
    return promocode


async def update_promocode(session: AsyncSession, promocode: PromoCode, data) -> PromoCode:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(promocode, field, value)
    await session.flush()
    return promocode


async def create_referral(session: AsyncSession, data) -> Referral:
    referral = Referral(**data.model_dump())
    session.add(referral)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Referral already exists") from exc
    return referral


async def update_referral(session: AsyncSession, referral: Referral, data) -> Referral:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(referral, field, value)
    await session.flush()
    return referral


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active or user.is_banned:
        raise HTTPException(status_code=403, detail="User is inactive or banned")
    return user


async def suspend_subscription(
    session: AsyncSession,
    subscription: Subscription,
    *,
    actor_user_id: int,
    ip_address: Optional[str],
    reason: Optional[str],
) -> Subscription:
    subscription.status = "suspended"
    await session.flush()
    await record_audit_event(
        session,
        actor_user_id=actor_user_id,
        action="subscription_suspend",
        target_type="subscription",
        target_id=str(subscription.id),
        metadata={"reason": reason} if reason else None,
        ip_address=ip_address,
    )
    return subscription


async def resume_subscription(
    session: AsyncSession,
    subscription: Subscription,
    *,
    actor_user_id: int,
    ip_address: Optional[str],
    note: Optional[str],
) -> Subscription:
    subscription.status = "active"
    await session.flush()
    await record_audit_event(
        session,
        actor_user_id=actor_user_id,
        action="subscription_resume",
        target_type="subscription",
        target_id=str(subscription.id),
        metadata={"note": note} if note else None,
        ip_address=ip_address,
    )
    return subscription


async def issue_promocode(
    session: AsyncSession,
    *,
    user: User,
    actor_user_id: int,
    ip_address: Optional[str],
    code: Optional[str],
    discount_percent: int,
    valid_for_hours: Optional[int],
) -> PromoCode:
    generated_code = code or token_urlsafe(8).upper()
    valid_until = None
    if valid_for_hours:
        valid_until = datetime.now(timezone.utc) + timedelta(hours=valid_for_hours)

    promocode = PromoCode(
        code=generated_code,
        discount_percent=discount_percent,
        valid_until=valid_until,
        issued_to_user_id=user.id,
    )
    session.add(promocode)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Promo code already exists") from exc

    await record_audit_event(
        session,
        actor_user_id=actor_user_id,
        action="promocode_issue",
        target_type="user",
        target_id=str(user.id),
        metadata={"code": promocode.code, "discount_percent": discount_percent},
        ip_address=ip_address,
    )
    return promocode


async def change_subscription_node(
    session: AsyncSession,
    *,
    subscription: Subscription,
    node: Node,
    actor_user_id: int,
    ip_address: Optional[str],
) -> Subscription:
    subscription.node_id = node.id
    await session.flush()
    await record_audit_event(
        session,
        actor_user_id=actor_user_id,
        action="subscription_change_node",
        target_type="subscription",
        target_id=str(subscription.id),
        metadata={"node_id": node.id},
        ip_address=ip_address,
    )
    return subscription


async def ban_user(
    session: AsyncSession,
    *,
    user: User,
    reason: Optional[str],
    actor_user_id: int,
    ip_address: Optional[str],
) -> User:
    user.is_banned = True
    user.is_active = False
    await session.flush()
    await record_audit_event(
        session,
        actor_user_id=actor_user_id,
        action="user_ban",
        target_type="user",
        target_id=str(user.id),
        metadata={"reason": reason} if reason else None,
        ip_address=ip_address,
    )
    return user
