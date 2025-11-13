from __future__ import annotations

from typing import Callable, Dict

from app.db.session import InMemorySession, get_session
from app.schemas.payments import PaymentConfirmRequest, PaymentResponse
from app.schemas.promocode import PromocodeApplyRequest, PromocodeApplyResponse
from app.schemas.subscription import SubscriptionStatusResponse
from app.schemas.trial import TrialStartRequest, TrialStartResponse
from app.services import subscription_service


class SimpleRouter:
    def __init__(self) -> None:
        self.routes: Dict[str, Callable[..., object]] = {}

    def post(self, path: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
        return self._register("POST", path)

    def get(self, path: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
        return self._register("GET", path)

    def _register(self, method: str, path: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
        def decorator(func: Callable[..., object]) -> Callable[..., object]:
            self.routes[f"{method} {path}"] = func
            return func

        return decorator


router = SimpleRouter()


def _resolve_session(db: InMemorySession | None) -> InMemorySession:
    return db or get_session()


@router.post("/payments/stars/confirm")
def confirm_payment(payload: PaymentConfirmRequest, db: InMemorySession | None = None) -> PaymentResponse:
    session = _resolve_session(db)
    payment = subscription_service.confirm_star_payment(
        session,
        user_id=payload.user_id,
        plan_id=payload.plan_id,
        transaction_id=payload.transaction_id,
        stars_used=payload.stars_used,
        amount_cents=payload.amount_cents,
    )
    subscription = payment.subscription
    return PaymentResponse(
        payment_id=payment.id or 0,
        subscription_id=subscription.id or 0 if subscription else 0,
        status=payment.status,
        next_billing_at=subscription.next_billing_at if subscription else None,
    )


@router.post("/trial/start")
def start_trial(payload: TrialStartRequest, db: InMemorySession | None = None) -> TrialStartResponse:
    session = _resolve_session(db)
    subscription = subscription_service.start_trial(session, payload.user_id, payload.plan_id)
    return TrialStartResponse(
        subscription_id=subscription.id or 0,
        trial_end=subscription.trial_end,
        end_date=subscription.end_date,
    )


@router.post("/promocode/apply")
def apply_promocode(payload: PromocodeApplyRequest, db: InMemorySession | None = None) -> PromocodeApplyResponse:
    session = _resolve_session(db)
    promo = subscription_service.apply_promocode(session, payload.user_id, payload.plan_id, payload.code)
    return PromocodeApplyResponse(
        code=promo.code,
        discount_percent=promo.discount_percent,
        bonus_days=promo.bonus_days,
        bonus_stars=promo.bonus_stars,
        valid_until=promo.valid_until,
    )


@router.get("/subs/status")
def subscription_status(user_id: int, db: InMemorySession | None = None) -> SubscriptionStatusResponse:
    session = _resolve_session(db)
    subscription = subscription_service.get_subscription_status(session, user_id)
    return SubscriptionStatusResponse(
        user_id=subscription.user_id or 0,
        plan_id=subscription.plan_id or 0,
        status=subscription.status.value,
        end_date=subscription.end_date,
        grace_until=subscription.grace_until,
        auto_renew=subscription.auto_renew,
    )
