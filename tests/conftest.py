import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Plan, User


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    user = User(id=1, email="user@example.com", full_name="User")
    plan = Plan(id=1, name="Basic", price_cents=1000, duration_days=30, trial_days=7)
    session.add_all([user, plan])
    session.commit()

    yield session

    session.close()
