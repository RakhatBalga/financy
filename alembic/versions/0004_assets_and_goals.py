"""investment positions, deposits, and financial goals

Revision ID: 0004_assets_and_goals
Revises: 0003_living_situation
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_assets_and_goals"
down_revision: str | None = "0003_living_situation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investment_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("average_price_usd", sa.Numeric(18, 4), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_investment_positions_user_id",
        "investment_positions",
        ["user_id"],
    )
    op.create_index(
        "ix_investment_positions_user_symbol",
        "investment_positions",
        ["user_id", "symbol"],
    )

    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("annual_rate", sa.Numeric(7, 3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_deposits_user_id", "deposits", ["user_id"])

    op.create_table(
        "financial_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("target_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "current_amount", sa.Numeric(18, 2), nullable=False, server_default="0"
        ),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_financial_goals_user_id", "financial_goals", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_financial_goals_user_id", table_name="financial_goals")
    op.drop_table("financial_goals")
    op.drop_index("ix_deposits_user_id", table_name="deposits")
    op.drop_table("deposits")
    op.drop_index(
        "ix_investment_positions_user_symbol", table_name="investment_positions"
    )
    op.drop_index("ix_investment_positions_user_id", table_name="investment_positions")
    op.drop_table("investment_positions")
