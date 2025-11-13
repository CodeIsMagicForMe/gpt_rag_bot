"""Shared dependencies for API routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .crud import get_entity
from .database import async_session_factory
from .models import User
from .schemas import TokenPayload
from .security import decode_access_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
) -> User:
    payload: TokenPayload = decode_access_token(token)
    user = await get_entity(session, User, payload.sub)
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


async def get_request_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
