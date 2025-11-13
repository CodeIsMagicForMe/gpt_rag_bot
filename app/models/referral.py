from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referee_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=True)
    bonus_stars = Column(Integer, default=0, nullable=False)
    bonus_paid = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    promocode = relationship("Promocode", back_populates="referrals")
