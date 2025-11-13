from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
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


def _ensure_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise ValueError("User not found")
    return user


def _ensure_plan(db: Session, plan_id: int) -> Plan:
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.is_active.is_(True)).one_or_none()
    if not plan:
        raise ValueError("Plan not found or inactive")
    return plan


def _apply_grace(subscription: Subscription, plan: Plan) -> None:
    subscription.grace_until = subscription.end_date + timedelta(days=plan.grace_period_days)


def _sync_status(subscription: Subscription) -> None:
    now = datetime.utcnow()
    if subscription.end_date >= now:
        subscription.status = SubscriptionStatus.ACTIVE
    elif subscription.grace_until and subscription.grace_until >= now:
        subscription.status = SubscriptionStatus.GRACE
    else:
        subscription.status = SubscriptionStatus.EXPIRED


def start_trial(db: Session, user_id: int, plan_id: int) -> Subscription:
    user = _ensure_user(db, user_id)
    plan = _ensure_plan(db, plan_id)
    if plan.trial_days <= 0:
        raise ValueError("Plan does not support trial")

    existing = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.plan_id == plan.id)
        .order_by(Subscription.end_date.desc())
        .first()
    )
    if existing and existing.trial_end:
        raise ValueError("Trial already used")

    start = datetime.utcnow()
    trial_end = start + timedelta(days=plan.trial_days)
    end = trial_end

    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start,
        end_date=end,
        trial_end=trial_end,
        auto_renew=True,
    )
    _apply_grace(subscription, plan)
    _sync_status(subscription)
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def apply_promocode(db: Session, user_id: int, plan_id: int, code: str) -> Promocode:
    _ensure_user(db, user_id)
    _ensure_plan(db, plan_id)
    promocode = (
        db.query(Promocode)
        .filter(Promocode.code == code.upper(), Promocode.is_active.is_(True))
        .one_or_none()
    )
    if not promocode:
        raise ValueError("Promocode not found")
    if promocode.valid_until and promocode.valid_until < datetime.utcnow():
        raise ValueError("Promocode expired")
    if promocode.used >= promocode.max_usages:
        raise ValueError("Promocode usage limit reached")

    promocode.used += 1
    db.add(promocode)
    db.commit()
    db.refresh(promocode)
    return promocode


def _create_or_extend_subscription(db: Session, user: User, plan: Plan) -> Subscription:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.plan_id == plan.id)
        .order_by(Subscription.end_date.desc())
        .first()
    )
    now = datetime.utcnow()
    if not subscription or subscription.status == SubscriptionStatus.EXPIRED:
        start = now
        end = now + timedelta(days=plan.duration_days)
        subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=start,
            end_date=end,
            auto_renew=plan.auto_renew,
        )
    else:
        base = subscription.end_date if subscription.end_date > now else now
        subscription.end_date = base + timedelta(days=plan.duration_days)

    _apply_grace(subscription, plan)
    subscription.next_billing_at = subscription.end_date if subscription.auto_renew else None
    _sync_status(subscription)
    db.add(subscription)
    db.flush()
    return subscription


def _award_referral_bonus(db: Session, user: User, payment: Payment) -> Optional[Referral]:
    referral = (
        db.query(Referral)
        .filter(Referral.referee_user_id == user.id, Referral.bonus_paid.is_(False))
        .one_or_none()
    )
    if not referral:
        return None

    bonus = int(payment.amount_cents * (settings.referral_bonus_percent / 100))
    referral.bonus_stars = bonus
    referral.bonus_paid = True
    user.stars_balance += bonus
    db.add_all([referral, user])
    return referral


def confirm_star_payment(
    db: Session,
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

    existing = db.query(Payment).filter(Payment.transaction_id == transaction_id).one_or_none()
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
    user.stars_balance -= stars_used

    db.add(payment)
    db.add(user)
    db.flush()
    subscription.last_payment_id = payment.id

    _award_referral_bonus(db, user, payment)

    db.commit()
    db.refresh(payment)
    db.refresh(subscription)
    return payment


def get_subscription_status(db: Session, user_id: int) -> Subscription:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.end_date.desc())
        .first()
    )
    if not subscription:
        raise ValueError("Subscription not found")
    _sync_status(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def process_auto_renewals(db: Session) -> list[Subscription]:
    now = datetime.utcnow()
    candidates = (
        db.query(Subscription)
        .filter(
            Subscription.auto_renew.is_(True),
            Subscription.next_billing_at.isnot(None),
            Subscription.next_billing_at <= now,
        )
        .all()
    )
    renewed: list[Subscription] = []
    for subscription in candidates:
        plan = subscription.plan
        user = subscription.user
        _create_or_extend_subscription(db, user, plan)
        renewed.append(subscription)
    db.commit()
    return renewed
