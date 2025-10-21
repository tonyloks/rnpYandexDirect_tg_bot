"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-10-21 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False, server_default="ru"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("tg_user_id"),
    )

    # Create yd_accounts table
    op.create_table(
        "yd_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("login", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Text(), nullable=True),
        sa.Column("goals_csv", sa.Text(), nullable=False),
        sa.Column(
            "goals_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("token_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("token_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_ok_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tg_user_id"], ["users.tg_user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create unique index on yd_accounts
    op.create_index(
        "ux_acc",
        "yd_accounts",
        ["tg_user_id", "login", sa.text("coalesce(account_id, '')")],
        unique=True,
    )

    # Create schedules table
    op.create_table(
        "schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("tz", sa.Text(), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["tg_user_id"], ["users.tg_user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create unique index on schedules
    op.create_index("ux_sched", "schedules", ["tg_user_id", "kind"], unique=True)

    # Create allowed_users table
    op.create_table(
        "allowed_users",
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("added_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("tg_user_id"),
    )

    # Create cache_budgets table (optional)
    op.create_table(
        "cache_budgets",
        sa.Column("account_ref", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_ref"], ["yd_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_ref"),
    )
    op.create_index("ix_cb_valid", "cache_budgets", ["valid_until"])

    # Create cache_stats table (optional)
    op.create_table(
        "cache_stats",
        sa.Column("account_ref", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_ref"], ["yd_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_ref", "period_key"),
    )
    op.create_index("ix_cs_valid", "cache_stats", ["valid_until"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("ix_cs_valid", table_name="cache_stats")
    op.drop_table("cache_stats")

    op.drop_index("ix_cb_valid", table_name="cache_budgets")
    op.drop_table("cache_budgets")

    op.drop_table("allowed_users")

    op.drop_index("ux_sched", table_name="schedules")
    op.drop_table("schedules")

    op.drop_index("ux_acc", table_name="yd_accounts")
    op.drop_table("yd_accounts")

    op.drop_table("users")
