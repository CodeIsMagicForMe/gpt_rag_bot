from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.payments import PaymentConfirmRequest, PaymentResponse
from app.schemas.promocode import PromocodeApplyRequest, PromocodeApplyResponse
from app.schemas.subscription import SubscriptionStatusResponse
from app.schemas.trial import TrialStartRequest, TrialStartResponse
from app.services import subscription_service

router = APIRouter()


@router.post("/payments/stars/confirm", response_model=PaymentResponse)
def confirm_payment(payload: PaymentConfirmRequest, db: Session = Depends(get_db)):
    try:
        payment = subscription_service.confirm_star_payment(
            db,
            user_id=payload.user_id,
            plan_id=payload.plan_id,
            transaction_id=payload.transaction_id,
            stars_used=payload.stars_used,
            amount_cents=payload.amount_cents,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    subscription = payment.subscription
    return PaymentResponse(
        payment_id=payment.id,
        subscription_id=subscription.id,
        status=payment.status,
        next_billing_at=subscription.next_billing_at,
    )


@router.post("/trial/start", response_model=TrialStartResponse)
def start_trial(payload: TrialStartRequest, db: Session = Depends(get_db)):
    try:
        subscription = subscription_service.start_trial(db, payload.user_id, payload.plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TrialStartResponse(
        subscription_id=subscription.id,
        trial_end=subscription.trial_end,
        end_date=subscription.end_date,
    )


@router.post("/promocode/apply", response_model=PromocodeApplyResponse)
def apply_promocode(payload: PromocodeApplyRequest, db: Session = Depends(get_db)):
    try:
        promo = subscription_service.apply_promocode(db, payload.user_id, payload.plan_id, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PromocodeApplyResponse(
        code=promo.code,
        discount_percent=promo.discount_percent,
        bonus_days=promo.bonus_days,
        bonus_stars=promo.bonus_stars,
        valid_until=promo.valid_until,
    )


@router.get("/subs/status", response_model=SubscriptionStatusResponse)
def subscription_status(user_id: int, db: Session = Depends(get_db)):
    try:
        subscription = subscription_service.get_subscription_status(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SubscriptionStatusResponse(
        user_id=subscription.user_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        end_date=subscription.end_date,
        grace_until=subscription.grace_until,
        auto_renew=subscription.auto_renew,
    )
