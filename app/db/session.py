from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Type, TypeVar

from app.models import Payment, Plan, Promocode, Referral, Subscription, User

T = TypeVar("T", User, Plan, Subscription, Payment, Promocode, Referral)


class InMemorySession:
    """A lightweight in-memory persistence layer for unit testing business logic."""

    def __init__(self) -> None:
        self._items: Dict[type, Dict[int, object]] = defaultdict(dict)
        self._counters: Dict[type, int] = defaultdict(int)

    # Generic helpers -----------------------------------------------------
    def _ensure_id(self, obj: T) -> int:
        current = getattr(obj, "id", None)
        if current is None:
            self._counters[type(obj)] += 1
            new_id = self._counters[type(obj)]
            setattr(obj, "id", new_id)
            return new_id
        return current

    def add(self, obj: T) -> None:
        obj_id = self._ensure_id(obj)
        self._items[type(obj)][obj_id] = obj

    def add_all(self, objs: Iterable[T]) -> None:
        for obj in objs:
            self.add(obj)

    def get(self, model: Type[T], obj_id: int) -> Optional[T]:
        return self._items.get(model, {}).get(obj_id)

    def list(self, model: Type[T]) -> List[T]:
        return list(self._items.get(model, {}).values())

    def filter(self, model: Type[T], predicate: Callable[[T], bool]) -> List[T]:
        return [item for item in self.list(model) if predicate(item)]

    # Persistence no-ops --------------------------------------------------
    def commit(self) -> None:  # pragma: no cover - maintained for API parity
        return

    def flush(self) -> None:  # pragma: no cover - maintained for API parity
        return

    def refresh(self, obj: T) -> None:  # pragma: no cover - maintained for API parity
        return

    def close(self) -> None:  # pragma: no cover - maintained for API parity
        return

    # Domain-specific helpers ---------------------------------------------
    def find_latest_subscription(self, user_id: int, plan_id: Optional[int] = None) -> Optional[Subscription]:
        subscriptions = self.filter(
            Subscription,
            lambda sub: sub.user_id == user_id and (plan_id is None or sub.plan_id == plan_id),
        )
        subscriptions.sort(key=lambda sub: sub.end_date, reverse=True)
        return subscriptions[0] if subscriptions else None

    def find_payment_by_transaction(self, transaction_id: str) -> Optional[Payment]:
        matches = self.filter(Payment, lambda pay: pay.transaction_id == transaction_id)
        return matches[0] if matches else None

    def find_promocode(self, code: str) -> Optional[Promocode]:
        matches = self.filter(Promocode, lambda promo: promo.code.upper() == code.upper())
        return matches[0] if matches else None

    def find_pending_referral(self, referee_user_id: int) -> Optional[Referral]:
        matches = self.filter(Referral, lambda ref: ref.referee_user_id == referee_user_id and not ref.bonus_paid)
        return matches[0] if matches else None

    def iter_auto_renewal_candidates(self, now) -> Iterator[Subscription]:
        for subscription in self.list(Subscription):
            if (
                subscription.auto_renew
                and subscription.next_billing_at is not None
                and subscription.next_billing_at <= now
            ):
                yield subscription


def get_session() -> InMemorySession:
    return InMemorySession()


def get_db() -> Iterator[InMemorySession]:
    db = get_session()
    try:
        yield db
    finally:
        db.close()
