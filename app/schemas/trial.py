from datetime import datetime
from pydantic import BaseModel


class TrialStartRequest(BaseModel):
    user_id: int
    plan_id: int


class TrialStartResponse(BaseModel):
    subscription_id: int
    trial_end: datetime
    end_date: datetime
