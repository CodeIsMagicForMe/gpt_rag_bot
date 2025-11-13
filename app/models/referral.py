from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Referral:
    id: int | None = None
    referrer_user_id: int | None = None
    referee_user_id: int | None = None
    promocode_id: int | None = None
    bonus_stars: int = 0
    bonus_paid: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    promocode: "Promocode" | None = None
