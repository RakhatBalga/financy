"""financial profile for personalized advice

Revision ID: 0007_financial_profile
Revises: 0006_deposit_interest
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_financial_profile"
down_revision: str | None = "0006_deposit_interest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("debt_balance", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("debt_annual_rate", sa.Numeric(7, 3), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("risk_tolerance", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "risk_tolerance")
    op.drop_column("users", "debt_annual_rate")
    op.drop_column("users", "debt_balance")
    op.drop_column("users", "age")
