from datetime import datetime
from pydantic import BaseModel


class PromocodeApplyRequest(BaseModel):
    user_id: int
    plan_id: int
    code: str


class PromocodeApplyResponse(BaseModel):
    code: str
    discount_percent: int
    bonus_days: int
    bonus_stars: int
    valid_until: datetime | None
