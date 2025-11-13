"""User management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import create_user, delete_entity, get_entity, list_entities, update_user
from ..models import User
from ..schemas import UserCreate, UserRead, UserUpdate
from ..audit import record_audit_event
from ..dependencies import get_current_active_user, get_db_session, get_request_ip

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[UserRead]:
    users = await list_entities(session, User, offset=offset, limit=limit)
    return [UserRead.model_validate(user) for user in users]


@router.post("/", response_model=UserRead, status_code=201)
async def create_user_endpoint(
    data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> UserRead:
    user = await create_user(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="user_create",
        target_type="user",
        target_id=str(user.id),
        metadata={"email": user.email},
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> UserRead:
    user = await get_entity(session, User, user_id)
    return UserRead.model_validate(user)


@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    data: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> UserRead:
    user = await get_entity(session, User, user_id)
    user = await update_user(session, user, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="user_update",
        target_type="user",
        target_id=str(user.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    user = await get_entity(session, User, user_id)
    await delete_entity(session, User, user_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="user_delete",
        target_type="user",
        target_id=str(user_id),
        metadata={"email": user.email},
        ip_address=ip,
    )
    await session.commit()
