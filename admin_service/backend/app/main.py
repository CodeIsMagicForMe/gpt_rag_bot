"""Entrypoint for the admin backend service."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import select

from .config import get_settings
from .database import Base, async_session_factory, engine
from .ip_allowlist import IPAllowListMiddleware
from .models import User
from .routers import actions, audit, auth, nodes, plans, promocodes, referrals, subscriptions, users
from .security import hash_password

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(IPAllowListMiddleware, allowed_ips=settings.allowed_ips)


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.email == settings.bootstrap_admin_email)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                user = User(
                    email=settings.bootstrap_admin_email,
                    full_name="Bootstrap Admin",
                    hashed_password=hash_password(settings.bootstrap_admin_password),
                    is_active=True,
                    is_banned=False,
                )
                session.add(user)
                await session.commit()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(nodes.router)
app.include_router(subscriptions.router)
app.include_router(promocodes.router)
app.include_router(referrals.router)
app.include_router(actions.router)
app.include_router(audit.router)
