"""advisor features: user.monthly_income, category.group_type

Revision ID: 0002_advisor
Revises: 0001_initial
Create Date: 2026-07-14

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_advisor"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Default categories -> 50/30/20 bucket (income categories left NULL).
_GROUPS = {
    "needs": ("Еда", "Транспорт", "Жильё", "Здоровье"),
    "wants": ("Развлечения", "Другое"),
}


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("monthly_income", sa.Numeric(14, 2), nullable=True),
    )
    op.add_column(
        "categories",
        sa.Column("group_type", sa.String(length=16), nullable=True),
    )

    # Backfill groups for already-created default categories.
    categories = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("group_type", sa.String),
        sa.column("is_default", sa.Boolean),
    )
    for group, names in _GROUPS.items():
        op.execute(
            categories.update()
            .where(categories.c.name.in_(names))
            .where(categories.c.is_default.is_(True))
            .values(group_type=group)
        )


def downgrade() -> None:
    op.drop_column("categories", "group_type")
    op.drop_column("users", "monthly_income")
