from datetime import datetime
from pydantic import BaseModel, Field


class PaymentConfirmRequest(BaseModel):
    user_id: int
    plan_id: int
    transaction_id: str
    stars_used: int = Field(ge=0)
    amount_cents: int = Field(ge=0)


class PaymentResponse(BaseModel):
    payment_id: int
    subscription_id: int
    status: str
    next_billing_at: datetime | None
