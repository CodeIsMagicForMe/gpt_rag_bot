from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PromocodeApplyRequest:
    user_id: int
    plan_id: int
    code: str


@dataclass(slots=True)
class PromocodeApplyResponse:
    code: str
    discount_percent: int
    bonus_days: int
    bonus_stars: int
    valid_until: datetime | None
