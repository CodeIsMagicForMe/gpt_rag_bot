from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Promocode:
    id: int | None = None
    code: str = ""
    discount_percent: int = 0
    bonus_days: int = 0
    bonus_stars: int = 0
    max_usages: int = 1
    used: int = 0
    valid_until: datetime | None = None
    is_active: bool = True
    referrals: List["Referral"] = field(default_factory=list)
