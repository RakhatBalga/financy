"""users.housing_is_free, users.food_is_free (onboarding)

Revision ID: 0003_living_situation
Revises: 0002_advisor
Create Date: 2026-07-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_living_situation"
down_revision: str | None = "0002_advisor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("housing_is_free", sa.Boolean(), nullable=True)
    )
    op.add_column("users", sa.Column("food_is_free", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "food_is_free")
    op.drop_column("users", "housing_is_free")
