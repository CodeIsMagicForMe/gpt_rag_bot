from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SubscriptionStatusResponse:
    user_id: int
    plan_id: int
    status: str
    end_date: datetime
    grace_until: datetime | None
    auto_renew: bool
