from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Promocode(Base):
    __tablename__ = "promocodes"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    discount_percent = Column(Integer, default=0, nullable=False)
    bonus_days = Column(Integer, default=0, nullable=False)
    bonus_stars = Column(Integer, default=0, nullable=False)
    max_usages = Column(Integer, default=1, nullable=False)
    used = Column(Integer, default=0, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    referrals = relationship("Referral", back_populates="promocode")
