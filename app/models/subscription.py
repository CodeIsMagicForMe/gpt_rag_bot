from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"


@dataclass
class Subscription:
    id: int | None = None
    user_id: int | None = None
    plan_id: int | None = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=datetime.utcnow)
    grace_until: datetime | None = None
    trial_end: datetime | None = None
    auto_renew: bool = True
    next_billing_at: datetime | None = None
    last_payment_id: int | None = None
    user: "User" | None = None
    plan: "Plan" | None = None
    payments: List["Payment"] = field(default_factory=list)
