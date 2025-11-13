from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Plan:
    id: int | None = None
    name: str = ""
    duration_days: int = 30
    price_cents: int = 0
    grace_period_days: int = 3
    trial_days: int = 0
    auto_renew: bool = True
    is_active: bool = True
    subscriptions: List["Subscription"] = field(default_factory=list)
