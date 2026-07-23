"""store the complete Kaspi installment schedule

Revision ID: 0011_installment_schedule
Revises: 0010_installment_banks
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_installment_schedule"
down_revision: str | None = "0010_installment_banks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("installment_kaspi_schedule", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "installment_kaspi_schedule")
