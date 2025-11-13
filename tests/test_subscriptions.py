from datetime import datetime, timedelta

import pytest

from app.models import SubscriptionStatus, User
from app.services import subscription_service


def test_start_trial(db_session):
    subscription = subscription_service.start_trial(db_session, user_id=1, plan_id=1)
    assert subscription.trial_end is not None
    assert subscription.status == SubscriptionStatus.ACTIVE


def test_promocode_usage_limit(db_session):
    from app.models import Promocode

    promo = Promocode(code="HELLO", discount_percent=10, max_usages=1)
    db_session.add(promo)
    db_session.commit()

    subscription_service.apply_promocode(db_session, user_id=1, plan_id=1, code="HELLO")
    with pytest.raises(ValueError):
        subscription_service.apply_promocode(db_session, user_id=1, plan_id=1, code="HELLO")


def test_confirm_payment_extends_subscription(db_session):
    user = db_session.get(User, 1)
    user.stars_balance = 100
    db_session.commit()

    payment = subscription_service.confirm_star_payment(
        db_session,
        user_id=1,
        plan_id=1,
        transaction_id="txn-1",
        stars_used=10,
        amount_cents=1000,
    )

    subscription = payment.subscription
    assert subscription is not None
    assert subscription.end_date > datetime.utcnow() + timedelta(days=25)


def test_subscription_status_reflects_grace(db_session):
    user = db_session.get(User, 1)
    user.stars_balance = 100
    db_session.commit()

    payment = subscription_service.confirm_star_payment(
        db_session,
        user_id=1,
        plan_id=1,
        transaction_id="txn-2",
        stars_used=10,
        amount_cents=1000,
    )
    subscription = payment.subscription
    subscription.end_date = datetime.utcnow() - timedelta(days=1)
    subscription.grace_until = datetime.utcnow() + timedelta(days=2)
    db_session.add(subscription)
    db_session.commit()

    status = subscription_service.get_subscription_status(db_session, user_id=1)
    assert status.status == SubscriptionStatus.GRACE


def test_process_auto_renewals(db_session):
    user = db_session.get(User, 1)
    user.stars_balance = 1000
    db_session.commit()

    payment = subscription_service.confirm_star_payment(
        db_session,
        user_id=1,
        plan_id=1,
        transaction_id="txn-3",
        stars_used=0,
        amount_cents=1000,
    )
    subscription = payment.subscription
    subscription.next_billing_at = datetime.utcnow() - timedelta(minutes=5)
    db_session.add(subscription)
    db_session.commit()

    renewed = subscription_service.process_auto_renewals(db_session)
    assert renewed
