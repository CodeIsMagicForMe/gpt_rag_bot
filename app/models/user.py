from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class User:
    id: int | None = None
    email: str = ""
    full_name: str | None = None
    stars_balance: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    subscriptions: List["Subscription"] = field(default_factory=list)
    payments: List["Payment"] = field(default_factory=list)
