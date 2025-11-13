from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TrialStartRequest:
    user_id: int
    plan_id: int


@dataclass(slots=True)
class TrialStartResponse:
    subscription_id: int
    trial_end: datetime | None
    end_date: datetime
