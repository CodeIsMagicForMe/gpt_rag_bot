from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    stars_used = Column(Integer, default=0, nullable=False)
    provider = Column(String, default="stars", nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="confirmed", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
