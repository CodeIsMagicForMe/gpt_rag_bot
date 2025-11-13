from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.db.session import InMemorySession
from app.models import (
    Payment,
    Plan,
    Promocode,
    Referral,
    Subscription,
    SubscriptionStatus,
    User,
)

settings = get_settings()


def _ensure_user(db: InMemorySession, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise ValueError("User not found")
    return user


def _ensure_plan(db: InMemorySession, plan_id: int) -> Plan:
    plan = db.get(Plan, plan_id)
    if not plan or not plan.is_active:
        raise ValueError("Plan not found or inactive")
    return plan


def _apply_grace(subscription: Subscription, plan: Plan) -> None:
    grace_days = plan.grace_period_days if plan.grace_period_days else settings.grace_period_days
    subscription.grace_until = subscription.end_date + timedelta(days=grace_days)


def _sync_status(subscription: Subscription) -> None:
    now = datetime.utcnow()
    if subscription.end_date >= now:
        subscription.status = SubscriptionStatus.ACTIVE
    elif subscription.grace_until and subscription.grace_until >= now:
        subscription.status = SubscriptionStatus.GRACE
    else:
        subscription.status = SubscriptionStatus.EXPIRED


def _persist_relationships(db: InMemorySession, subscription: Subscription, user: User, plan: Plan) -> None:
    subscription.user_id = user.id
    subscription.plan_id = plan.id
    subscription.user = user
    subscription.plan = plan
    if subscription not in user.subscriptions:
        user.subscriptions.append(subscription)
    if subscription not in plan.subscriptions:
        plan.subscriptions.append(subscription)
    db.add(subscription)


def _create_subscription(user: User, plan: Plan, *, start: datetime, end: datetime) -> Subscription:
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start,
        end_date=end,
        auto_renew=plan.auto_renew,
    )
    subscription.user = user
    subscription.plan = plan
    return subscription


def start_trial(db: InMemorySession, user_id: int, plan_id: int) -> Subscription:
    user = _ensure_user(db, user_id)
    plan = _ensure_plan(db, plan_id)
    if plan.trial_days <= 0:
        raise ValueError("Plan does not support trial")

    existing = db.find_latest_subscription(user.id, plan.id)
    if existing and existing.trial_end:
        raise ValueError("Trial already used")

    start = datetime.utcnow()
    trial_end = start + timedelta(days=plan.trial_days)
    subscription = _create_subscription(user, plan, start=start, end=trial_end)
    subscription.trial_end = trial_end
    _apply_grace(subscription, plan)
    _sync_status(subscription)
    _persist_relationships(db, subscription, user, plan)
    db.commit()
    return subscription


def apply_promocode(db: InMemorySession, user_id: int, plan_id: int, code: str) -> Promocode:
    _ensure_user(db, user_id)
    _ensure_plan(db, plan_id)
    promocode = db.find_promocode(code)
    if not promocode or not promocode.is_active:
        raise ValueError("Promocode not found")
    if promocode.valid_until and promocode.valid_until < datetime.utcnow():
        raise ValueError("Promocode expired")
    if promocode.used >= promocode.max_usages:
        raise ValueError("Promocode usage limit reached")

    promocode.used += 1
    db.add(promocode)
    db.commit()
    return promocode


def _create_or_extend_subscription(db: InMemorySession, user: User, plan: Plan) -> Subscription:
    subscription = db.find_latest_subscription(user.id, plan.id)
    now = datetime.utcnow()

    if not subscription or subscription.status == SubscriptionStatus.EXPIRED:
        subscription = _create_subscription(user, plan, start=now, end=now + timedelta(days=plan.duration_days))
    else:
        base = subscription.end_date if subscription.end_date > now else now
        subscription.end_date = base + timedelta(days=plan.duration_days)

    _apply_grace(subscription, plan)
    subscription.user = user
    subscription.plan = plan
    subscription.auto_renew = plan.auto_renew
    subscription.next_billing_at = subscription.end_date if subscription.auto_renew else None
    _sync_status(subscription)
    _persist_relationships(db, subscription, user, plan)
    db.flush()
    return subscription


def _award_referral_bonus(db: InMemorySession, user: User, payment: Payment) -> Optional[Referral]:
    referral = db.find_pending_referral(user.id)
    if not referral:
        return None

    bonus = int(payment.amount_cents * (settings.referral_bonus_percent / 100))
    referral.bonus_stars = bonus
    referral.bonus_paid = True
    user.stars_balance += bonus
    db.add(referral)
    db.add(user)
    return referral


def confirm_star_payment(
    db: InMemorySession,
    *,
    user_id: int,
    plan_id: int,
    transaction_id: str,
    stars_used: int,
    amount_cents: int,
) -> Payment:
    user = _ensure_user(db, user_id)
    plan = _ensure_plan(db, plan_id)

    if stars_used > user.stars_balance:
        raise ValueError("Not enough stars")

    existing = db.find_payment_by_transaction(transaction_id)
    if existing:
        return existing

    subscription = _create_or_extend_subscription(db, user, plan)

    payment = Payment(
        user_id=user.id,
        subscription_id=subscription.id,
        amount_cents=amount_cents,
        stars_used=stars_used,
        transaction_id=transaction_id,
    )
    db.add(payment)
    payment.user = user
    payment.subscription = subscription
    subscription.last_payment_id = payment.id
    db.add(subscription)
    subscription.payments.append(payment)
    user.payments.append(payment)

    user.stars_balance -= stars_used
    db.add(user)

    _award_referral_bonus(db, user, payment)

    db.commit()
    return payment


def get_subscription_status(db: InMemorySession, user_id: int) -> Subscription:
    subscription = db.find_latest_subscription(user_id)
    if not subscription:
        raise ValueError("Subscription not found")
    _sync_status(subscription)
    db.commit()
    return subscription


def process_auto_renewals(db: InMemorySession) -> list[Subscription]:
    now = datetime.utcnow()
    renewed: list[Subscription] = []
    for subscription in list(db.iter_auto_renewal_candidates(now)):
        plan = _ensure_plan(db, subscription.plan_id or 0)
        user = _ensure_user(db, subscription.user_id or 0)
        _create_or_extend_subscription(db, user, plan)
        renewed.append(subscription)
    db.commit()
    return renewed
