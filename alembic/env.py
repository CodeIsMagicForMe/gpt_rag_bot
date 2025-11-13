from __future__ import annotations

from alembic import context

from app.db.base import describe_schema

SCHEMA = describe_schema()


def _emit(message: str) -> None:
    config = getattr(context, "config", None)
    buffer = getattr(config, "output_buffer", None) if config else None
    if buffer is not None:
        buffer.write(message + "\n")
    else:  # pragma: no cover - fallback when Alembic context is absent
        print(message)


def run_migrations_offline() -> None:
    _emit("Alembic offline stub. The following tables would be created:")
    for table in SCHEMA.values():
        columns = ", ".join(column.name for column in table.columns)
        _emit(f"- {table.name}: {columns}")


def run_migrations_online() -> None:
    _emit("Alembic online execution is not available in this environment.")
    run_migrations_offline()
