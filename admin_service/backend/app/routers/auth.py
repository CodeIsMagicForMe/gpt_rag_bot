"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import authenticate_user
from ..dependencies import get_db_session
from ..schemas import LoginRequest, Token
from ..security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest, session: AsyncSession = Depends(get_db_session)
) -> Token:
    user = await authenticate_user(session, data.email, data.password)
    token, expires_in = create_access_token(user.id)
    return Token(access_token=token, expires_in=expires_in)
