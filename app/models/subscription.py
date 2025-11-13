from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Enum as PgEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(PgEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False)
    grace_until = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    next_billing_at = Column(DateTime, nullable=True)
    last_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
