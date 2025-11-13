from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Payment:
    id: int | None = None
    user_id: int | None = None
    subscription_id: int | None = None
    amount_cents: int = 0
    currency: str = "USD"
    stars_used: int = 0
    provider: str = "stars"
    transaction_id: str = ""
    status: str = "confirmed"
    created_at: datetime = field(default_factory=datetime.utcnow)
    user: "User" | None = None
    subscription: "Subscription" | None = None
