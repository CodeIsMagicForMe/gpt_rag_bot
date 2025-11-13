from __future__ import annotations

from dataclasses import dataclass

from app.api.routes import router
from app.core.config import get_settings


@dataclass
class SubscriptionsApp:
    title: str
    routes: dict[str, object]


settings = get_settings()
app = SubscriptionsApp(title=settings.app_name, routes=router.routes)


def root() -> dict[str, str]:
    return {"message": "Subscriptions service is running"}
