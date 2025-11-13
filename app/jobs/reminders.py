from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List
from urllib import request, parse

from app.core.config import get_settings
from app.db.session import InMemorySession
from app.models import Subscription, SubscriptionStatus

settings = get_settings()


class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}" if token else ""

    def send_message(self, chat_id: int | str, text: str) -> None:
        if not self.token:
            return
        payload = parse.urlencode({"chat_id": chat_id, "text": text}).encode()
        req = request.Request(f"{self.base_url}/sendMessage", data=payload)
        
        try:
            request.urlopen(req, timeout=10)
        except Exception:
            # Network might be unavailable during tests.
            pass


def iter_expiring_subscriptions(db: InMemorySession) -> Iterable[Subscription]:
    now = datetime.utcnow()
    window_end = now + timedelta(days=settings.reminder_days_before)
    for subscription in db.list(Subscription):
        if subscription.status != SubscriptionStatus.ACTIVE:
            continue
        if subscription.end_date <= window_end:
            yield subscription


def send_subscription_reminders(
    db: InMemorySession,
    chat_id_lookup: Dict[int, str | int],
    client: TelegramClient | None = None,
) -> List[int]:
    client = client or TelegramClient(settings.telegram_bot_token)
    notified_users: List[int] = []
    for subscription in iter_expiring_subscriptions(db):
        chat_id = chat_id_lookup.get(subscription.user_id or 0)
        if not chat_id:
            continue
        days_left = max((subscription.end_date - datetime.utcnow()).days, 0)
        text = (
            f"Подписка по плану {subscription.plan.name if subscription.plan else subscription.plan_id} "
            f"заканчивается через {days_left} дней. Продлите доступ, чтобы не потерять бонусы!"
        )
        client.send_message(chat_id, text)
        notified_users.append(subscription.user_id or 0)
    return notified_users
