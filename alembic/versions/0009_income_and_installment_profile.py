"""official income timing and installment schedule

Revision ID: 0009_income_installments
Revises: 0008_installments_mortgage
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_income_installments"
down_revision: str | None = "0008_installments_mortgage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("official_salary_monthly", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("official_stipend_monthly", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "mortgage_payment_limit_percent",
            sa.Numeric(7, 3),
            nullable=True,
        ),
    )
    op.add_column("users", sa.Column("salary_day", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("salary_weekend_rule", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stipend_timing", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("installment_balance_primary", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("installment_balance_secondary", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("installment_end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("installment_august_payment", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("installment_september_payment", sa.Numeric(18, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "installment_september_payment")
    op.drop_column("users", "installment_august_payment")
    op.drop_column("users", "installment_end_date")
    op.drop_column("users", "installment_balance_secondary")
    op.drop_column("users", "installment_balance_primary")
    op.drop_column("users", "stipend_timing")
    op.drop_column("users", "salary_weekend_rule")
    op.drop_column("users", "salary_day")
    op.drop_column("users", "mortgage_payment_limit_percent")
    op.drop_column("users", "official_stipend_monthly")
    op.drop_column("users", "official_salary_monthly")
