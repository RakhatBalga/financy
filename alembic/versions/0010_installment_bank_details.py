"""installment bank details

Revision ID: 0010_installment_banks
Revises: 0009_income_installments
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_installment_banks"
down_revision: str | None = "0009_income_installments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("installment_kaspi_end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "installment_halyk_monthly_payment",
            sa.Numeric(18, 2),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column("installment_halyk_end_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "installment_halyk_end_date")
    op.drop_column("users", "installment_halyk_monthly_payment")
    op.drop_column("users", "installment_kaspi_end_date")
