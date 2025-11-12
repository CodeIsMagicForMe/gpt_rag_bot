from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def _build_engine() -> tuple:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./provisioner.db")
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    session_factory = scoped_session(
        sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    )
    return engine, session_factory


ENGINE, SessionLocal = _build_engine()


@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
