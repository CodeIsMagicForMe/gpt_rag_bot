"""create subscription related tables"""
from alembic import op
import sqlalchemy as sa

revision = "20240527_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("stars_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("grace_period_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )

    op.create_table(
        "promocodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("discount_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_usages", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.Enum("active", "grace", "expired", name="subscriptionstatus"), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("grace_until", sa.DateTime(), nullable=True),
        sa.Column("trial_end", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("next_billing_at", sa.DateTime(), nullable=True),
        sa.Column("last_payment_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id")),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("stars_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(), nullable=False, server_default="stars"),
        sa.Column("transaction_id", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("referee_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("promocode_id", sa.Integer(), sa.ForeignKey("promocodes.id")),
        sa.Column("bonus_stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_paid", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("referrals")
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("promocodes")
    op.drop_table("plans")
    op.drop_table("users")
    sa.Enum(name="subscriptionstatus").drop(op.get_bind(), checkfirst=False)
