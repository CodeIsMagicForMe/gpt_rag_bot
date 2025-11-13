from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Subscriptions Service"
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        env="DATABASE_URL",
    )
    telegram_bot_token: str = Field("", env="TELEGRAM_BOT_TOKEN")
    reminder_days_before: int = 3
    referral_bonus_percent: float = 10.0
    grace_period_days: int = 3

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
