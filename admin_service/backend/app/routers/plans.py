"""Plan management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit_event
from ..crud import create_plan, delete_entity, get_entity, list_entities, update_plan
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import Plan, User
from ..schemas import PlanCreate, PlanRead, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanRead])
async def list_plans(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[PlanRead]:
    plans = await list_entities(session, Plan, offset=offset, limit=limit)
    return [PlanRead.model_validate(plan) for plan in plans]


@router.post("/", response_model=PlanRead, status_code=201)
async def create_plan_endpoint(
    data: PlanCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> PlanRead:
    plan = await create_plan(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="plan_create",
        target_type="plan",
        target_id=str(plan.id),
        metadata=data.model_dump(),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(plan)
    return PlanRead.model_validate(plan)


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan_endpoint(
    plan_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> PlanRead:
    plan = await get_entity(session, Plan, plan_id)
    return PlanRead.model_validate(plan)


@router.put("/{plan_id}", response_model=PlanRead)
async def update_plan_endpoint(
    plan_id: int,
    data: PlanUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> PlanRead:
    plan = await get_entity(session, Plan, plan_id)
    plan = await update_plan(session, plan, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="plan_update",
        target_type="plan",
        target_id=str(plan.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(plan)
    return PlanRead.model_validate(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan_endpoint(
    plan_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    plan = await get_entity(session, Plan, plan_id)
    await delete_entity(session, Plan, plan_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="plan_delete",
        target_type="plan",
        target_id=str(plan_id),
        metadata={"name": plan.name},
        ip_address=ip,
    )
    await session.commit()
