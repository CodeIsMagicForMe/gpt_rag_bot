from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ColumnDefinition:
    name: str
    type: str
    nullable: bool = True
    extras: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class TableDefinition:
    name: str
    columns: List[ColumnDefinition] = field(default_factory=list)


SCHEMA_DEFINITION: Dict[str, TableDefinition] = {
    "users": TableDefinition(
        name="users",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("email", "string", nullable=False, extras={"unique": True}),
            ColumnDefinition("full_name", "string"),
            ColumnDefinition("stars_balance", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("is_active", "boolean", nullable=False, extras={"default": True}),
            ColumnDefinition("created_at", "datetime", nullable=False),
        ],
    ),
    "plans": TableDefinition(
        name="plans",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("name", "string", nullable=False, extras={"unique": True}),
            ColumnDefinition("duration_days", "integer", nullable=False, extras={"default": 30}),
            ColumnDefinition("price_cents", "integer", nullable=False),
            ColumnDefinition("grace_period_days", "integer", nullable=False, extras={"default": 3}),
            ColumnDefinition("trial_days", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("auto_renew", "boolean", nullable=False, extras={"default": True}),
            ColumnDefinition("is_active", "boolean", nullable=False, extras={"default": True}),
        ],
    ),
    "subscriptions": TableDefinition(
        name="subscriptions",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("user_id", "integer", nullable=False),
            ColumnDefinition("plan_id", "integer", nullable=False),
            ColumnDefinition("status", "enum", nullable=False, extras={"values": ["active", "grace", "expired"]}),
            ColumnDefinition("start_date", "datetime", nullable=False),
            ColumnDefinition("end_date", "datetime", nullable=False),
            ColumnDefinition("grace_until", "datetime"),
            ColumnDefinition("trial_end", "datetime"),
            ColumnDefinition("auto_renew", "boolean", nullable=False, extras={"default": True}),
            ColumnDefinition("next_billing_at", "datetime"),
            ColumnDefinition("last_payment_id", "integer"),
        ],
    ),
    "payments": TableDefinition(
        name="payments",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("user_id", "integer", nullable=False),
            ColumnDefinition("subscription_id", "integer"),
            ColumnDefinition("amount_cents", "integer", nullable=False),
            ColumnDefinition("currency", "string", nullable=False, extras={"default": "USD"}),
            ColumnDefinition("stars_used", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("provider", "string", nullable=False, extras={"default": "stars"}),
            ColumnDefinition("transaction_id", "string", nullable=False, extras={"unique": True}),
            ColumnDefinition("status", "string", nullable=False, extras={"default": "confirmed"}),
            ColumnDefinition("created_at", "datetime", nullable=False),
        ],
    ),
    "promocodes": TableDefinition(
        name="promocodes",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("code", "string", nullable=False, extras={"unique": True}),
            ColumnDefinition("discount_percent", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("bonus_days", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("bonus_stars", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("max_usages", "integer", nullable=False, extras={"default": 1}),
            ColumnDefinition("used", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("valid_until", "datetime"),
            ColumnDefinition("is_active", "boolean", nullable=False, extras={"default": True}),
        ],
    ),
    "referrals": TableDefinition(
        name="referrals",
        columns=[
            ColumnDefinition("id", "integer", nullable=False),
            ColumnDefinition("referrer_user_id", "integer", nullable=False),
            ColumnDefinition("referee_user_id", "integer", nullable=False),
            ColumnDefinition("promocode_id", "integer"),
            ColumnDefinition("bonus_stars", "integer", nullable=False, extras={"default": 0}),
            ColumnDefinition("bonus_paid", "boolean", nullable=False, extras={"default": False}),
            ColumnDefinition("created_at", "datetime", nullable=False),
        ],
    ),
}


def describe_schema() -> Dict[str, TableDefinition]:
    return SCHEMA_DEFINITION
