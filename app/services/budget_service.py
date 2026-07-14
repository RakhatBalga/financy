"""Use-case service for monthly budgets and limit checks."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransactionType, User
from app.repositories.budget_repo import BudgetRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.transaction_repo import TransactionRepository
from app.services import periods

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class BudgetAlert:
    """A single over-threshold budget notification."""

    category_name: str
    spent: float
    limit: float
    ratio: float  # spent / limit
    level: str  # "warning" (>=80%) or "exceeded" (>=100%)


class BudgetService:
    """Sets monthly limits and evaluates them against actual spending."""

    WARNING_THRESHOLD = 0.8
    EXCEEDED_THRESHOLD = 1.0

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._budgets = BudgetRepository(session)
        self._categories = CategoryRepository(session)
        self._transactions = TransactionRepository(session)

    async def set_budget(
        self, user_id: int, category_name: str, monthly_limit: float
    ) -> str:
        """Set (or overwrite) the current-month limit for a category.

        Returns the resolved category name. Raises :class:`ValueError` if the
        limit is not positive.
        """
        if monthly_limit <= 0:
            raise ValueError("monthly limit must be positive")

        category = await self._categories.get_or_create(user_id, category_name)
        await self._budgets.upsert(
            user_id=user_id,
            category_id=category.id,
            monthly_limit=monthly_limit,
            month=periods.current_month_key(),
        )
        await self._session.commit()
        log.info(
            "budget_set",
            user_id=user_id,
            category=category.name,
            limit=monthly_limit,
        )
        return category.name

    async def check_user(self, user: User) -> list[BudgetAlert]:
        """Return budget alerts for the user's current-month spending.

        An alert is produced when spending reaches 80% (warning) or 100%
        (exceeded) of the category limit. Read-only.
        """
        month = periods.current_month_key()
        start, end = periods.month_range()
        budgets = await self._budgets.list_for_month(user.id, month)

        alerts: list[BudgetAlert] = []
        for budget in budgets:
            spent = await self._transactions.total_for_category(
                user.id,
                budget.category_id,
                TransactionType.expense,
                start,
                end,
            )
            limit = float(budget.monthly_limit)
            ratio = spent / limit if limit else 0.0
            if ratio >= self.EXCEEDED_THRESHOLD:
                level = "exceeded"
            elif ratio >= self.WARNING_THRESHOLD:
                level = "warning"
            else:
                continue

            alerts.append(
                BudgetAlert(
                    category_name=budget.category.name,
                    spent=spent,
                    limit=limit,
                    ratio=ratio,
                    level=level,
                )
            )
        return alerts
