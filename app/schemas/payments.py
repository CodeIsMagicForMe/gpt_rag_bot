from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PaymentConfirmRequest:
    user_id: int
    plan_id: int
    transaction_id: str
    stars_used: int = 0
    amount_cents: int = 0

    def __post_init__(self) -> None:
        if self.stars_used < 0:
            raise ValueError("stars_used must be non-negative")
        if self.amount_cents < 0:
            raise ValueError("amount_cents must be non-negative")


@dataclass(slots=True)
class PaymentResponse:
    payment_id: int
    subscription_id: int
    status: str
    next_billing_at: datetime | None
