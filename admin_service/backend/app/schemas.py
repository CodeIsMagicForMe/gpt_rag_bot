"""Pydantic schemas for request and response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: int
    exp: datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_banned: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PlanRead(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NodeBase(BaseModel):
    name: str
    address: str
    capacity: int = 0
    is_active: bool = True


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class NodeRead(NodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    node_id: Optional[int] = None
    status: str = "active"
    start_date: datetime
    end_date: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    node_id: Optional[int] = None
    status: Optional[str] = None
    end_date: Optional[datetime] = None


class SubscriptionRead(SubscriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromoCodeBase(BaseModel):
    code: str
    discount_percent: int = Field(ge=0, le=100)
    valid_until: Optional[datetime] = None
    is_active: bool = True
    issued_to_user_id: Optional[int] = None


class PromoCodeCreate(PromoCodeBase):
    pass


class PromoCodeUpdate(BaseModel):
    discount_percent: Optional[int] = Field(default=None, ge=0, le=100)
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    issued_to_user_id: Optional[int] = None


class PromoCodeRead(PromoCodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReferralBase(BaseModel):
    referrer_id: int
    referred_id: int
    reward_granted: bool = False


class ReferralCreate(ReferralBase):
    pass


class ReferralUpdate(BaseModel):
    reward_granted: Optional[bool] = None


class ReferralRead(ReferralBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogRead(BaseModel):
    id: int
    actor_user_id: Optional[int]
    action: str
    target_type: str
    target_id: str
    metadata: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class IssuePromoCodeRequest(BaseModel):
    user_id: int
    code: Optional[str] = None
    discount_percent: int = Field(ge=0, le=100, default=10)
    valid_for_hours: Optional[int] = Field(default=None, ge=1)


class ChangeNodeRequest(BaseModel):
    subscription_id: int
    node_id: int


class BanUserRequest(BaseModel):
    user_id: int
    reason: Optional[str] = None


class SuspendSubscriptionRequest(BaseModel):
    subscription_id: int
    reason: Optional[str] = None


class ResumeSubscriptionRequest(BaseModel):
    subscription_id: int
    note: Optional[str] = None
