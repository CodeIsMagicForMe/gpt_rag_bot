from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, BaseSettings, Field, HttpUrl


class SubscriptionPlan(BaseModel):
    title: str = Field(default="Подписка на 30 дней")
    description: str = Field(default="Доступ к VPN на месяц")
    price_stars: int = Field(default=149, ge=1)
    payload: str = Field(default="subscription_extend")


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_chat_id: int = Field(..., alias="ADMIN_CHAT_ID")
    billing_base_url: HttpUrl = Field(..., alias="BILLING_BASE_URL")
    provisioner_base_url: HttpUrl = Field(..., alias="PROVISIONER_BASE_URL")
    payment_provider_token: Optional[str] = Field(None, alias="PAYMENT_PROVIDER_TOKEN")
    subscription_plan: SubscriptionPlan = SubscriptionPlan()
    faq_text: str = Field(
        default=(
            "❓ <b>FAQ</b>\n\n"
            "<b>Как подключиться?</b>\nПолучите конфиг или QR в личном кабинете.\n\n"
            "<b>Сколько действует подписка?</b>\n" "30 дней с момента активации."
        )
    )
    terms_url: HttpUrl = Field(default="https://example.com/terms", alias="TERMS_URL")
    privacy_url: HttpUrl = Field(default="https://example.com/privacy", alias="PRIVACY_URL")
    data_usage_notice: str = Field(
        default="ℹ️ Мы храним только ваш Telegram ID и технические метаданные, необходимые для выдачи доступа."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@dataclass
class Config:
    bot_token: str
    admin_chat_id: int
    billing_base_url: str
    provisioner_base_url: str
    payment_provider_token: Optional[str]
    subscription_plan: SubscriptionPlan
    faq_text: str
    terms_url: str
    privacy_url: str
    data_usage_notice: str


@lru_cache()
def load_config() -> Config:
    settings = Settings()  # type: ignore[arg-type]
    return Config(
        bot_token=settings.bot_token,
        admin_chat_id=settings.admin_chat_id,
        billing_base_url=settings.billing_base_url.rstrip("/"),
        provisioner_base_url=settings.provisioner_base_url.rstrip("/"),
        payment_provider_token=settings.payment_provider_token,
        subscription_plan=settings.subscription_plan,
        faq_text=settings.faq_text,
        terms_url=str(settings.terms_url),
        privacy_url=str(settings.privacy_url),
        data_usage_notice=settings.data_usage_notice,
    )
