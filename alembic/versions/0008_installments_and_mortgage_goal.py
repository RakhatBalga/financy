"""installment profile and mortgage-backed goals

Revision ID: 0008_installments_mortgage
Revises: 0007_financial_profile
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_installments_mortgage"
down_revision: str | None = "0007_financial_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("obligation_type", sa.String(length=24), nullable=True),
    )
    op.add_column(
        "financial_goals",
        sa.Column("financing_program", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "financial_goals",
        sa.Column("down_payment_percent", sa.Numeric(7, 3), nullable=True),
    )
    op.add_column(
        "financial_goals",
        sa.Column("loan_annual_rate", sa.Numeric(7, 3), nullable=True),
    )
    op.add_column(
        "financial_goals",
        sa.Column("loan_term_years", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_goals", "loan_term_years")
    op.drop_column("financial_goals", "loan_annual_rate")
    op.drop_column("financial_goals", "down_payment_percent")
    op.drop_column("financial_goals", "financing_program")
    op.drop_column("users", "obligation_type")
