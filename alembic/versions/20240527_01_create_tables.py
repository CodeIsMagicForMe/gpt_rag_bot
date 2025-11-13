"""Documented schema for subscription tables."""

from __future__ import annotations

from app.db.base import SCHEMA_DEFINITION

revision = "20240527_01"
down_revision = None
branch_labels = None
depends_on = None


def describe_tables() -> dict[str, object]:
    """Return the static schema description used for documentation purposes."""
    return SCHEMA_DEFINITION
