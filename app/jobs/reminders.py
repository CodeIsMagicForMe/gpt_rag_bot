from datetime import datetime, timedelta
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Subscription, SubscriptionStatus

settings = get_settings()


class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id: int | str, text: str) -> None:
        if not self.token:
            # In tests we simply no-op
            return
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        httpx.post(url, json=payload, timeout=10.0)


def iter_expiring_subscriptions(db: Session) -> Iterable[Subscription]:
    now = datetime.utcnow()
    window_end = now + timedelta(days=settings.reminder_days_before)
    return (
        db.query(Subscription)
        .filter(Subscription.end_date <= window_end, Subscription.status == SubscriptionStatus.ACTIVE)
        .all()
    )


def send_subscription_reminders(db: Session, chat_id_lookup: dict[int, str | int], client: TelegramClient | None = None) -> list[int]:
    client = client or TelegramClient(settings.telegram_bot_token)
    notified_users: list[int] = []
    for subscription in iter_expiring_subscriptions(db):
        chat_id = chat_id_lookup.get(subscription.user_id)
        if not chat_id:
            continue
        days = (subscription.end_date - datetime.utcnow()).days
        text = (
            f"Подписка по плану {subscription.plan.name} заканчивается через {max(days, 0)} дней. "
            "Продлите доступ, чтобы не потерять бонусы!"
        )
        client.send_message(chat_id, text)
        notified_users.append(subscription.user_id)
    return notified_users
