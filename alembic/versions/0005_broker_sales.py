"""broker account snapshot and realized stock sales

Revision ID: 0005_broker_sales
Revises: 0004_assets_and_goals
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_broker_sales"
down_revision: str | None = "0004_assets_and_goals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cash_usd", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column(
            "realized_pnl_usd", sa.Numeric(18, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "transaction_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("reported_total_pnl_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("reported_total_pnl_percent", sa.Numeric(8, 3), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_broker_accounts_user_id"),
    )
    op.create_index("ix_broker_accounts_user_id", "broker_accounts", ["user_id"])

    op.create_table(
        "stock_sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("average_buy_price_usd", sa.Numeric(18, 4), nullable=False),
        sa.Column("sell_price_usd", sa.Numeric(18, 4), nullable=False),
        sa.Column("realized_pnl_usd", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_stock_sales_user_id", "stock_sales", ["user_id"])
    op.create_index(
        "ix_stock_sales_user_created", "stock_sales", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_stock_sales_user_created", table_name="stock_sales")
    op.drop_index("ix_stock_sales_user_id", table_name="stock_sales")
    op.drop_table("stock_sales")
    op.drop_index("ix_broker_accounts_user_id", table_name="broker_accounts")
    op.drop_table("broker_accounts")
