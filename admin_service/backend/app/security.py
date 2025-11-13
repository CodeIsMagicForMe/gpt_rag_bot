"""Security helpers for password hashing and JWT handling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings
from .schemas import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: int, expires_minutes: int | None = None) -> tuple[str, int]:
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    expire_delta = timedelta(minutes=expire_minutes)
    expire = datetime.now(timezone.utc) + expire_delta
    payload = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt, int(expire_delta.total_seconds())


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload.model_validate(payload)
    except JWTError as exc:  # pragma: no cover - library errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc
