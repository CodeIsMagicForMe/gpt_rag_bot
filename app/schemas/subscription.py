from datetime import datetime
from pydantic import BaseModel


class SubscriptionStatusResponse(BaseModel):
    user_id: int
    plan_id: int | None
    status: str
    end_date: datetime | None
    grace_until: datetime | None
    auto_renew: bool
