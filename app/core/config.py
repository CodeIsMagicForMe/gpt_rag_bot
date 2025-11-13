from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(slots=True)
class Settings:
    app_name: str = "Subscriptions Service"
    database_url: str = "memory://subscriptions"
    telegram_bot_token: str = ""
    reminder_days_before: int = 3
    referral_bonus_percent: float = 10.0
    grace_period_days: int = 3

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            app_name=os.getenv("APP_NAME", defaults.app_name),
            database_url=os.getenv("DATABASE_URL", defaults.database_url),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", defaults.telegram_bot_token),
            reminder_days_before=int(os.getenv("REMINDER_DAYS_BEFORE", defaults.reminder_days_before)),
            referral_bonus_percent=float(
                os.getenv("REFERRAL_BONUS_PERCENT", defaults.referral_bonus_percent)
            ),
            grace_period_days=int(os.getenv("GRACE_PERIOD_DAYS", defaults.grace_period_days)),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
