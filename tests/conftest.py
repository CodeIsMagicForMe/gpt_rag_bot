import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from app.db.session import InMemorySession
from app.models import Plan, User


@pytest.fixture()
def db_session():
    session = InMemorySession()
    user = User(id=1, email="user@example.com", full_name="User", stars_balance=0)
    plan = Plan(
        id=1,
        name="Basic",
        price_cents=1000,
        duration_days=30,
        trial_days=7,
        grace_period_days=3,
    )
    session.add_all([user, plan])
    yield session
    session.close()
