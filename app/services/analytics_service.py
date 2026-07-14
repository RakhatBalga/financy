"""Pure aggregation over transactions — period reports and weekly digests.

No AI at read time: everything here is deterministic SQL aggregation plus
arithmetic, so reports are cheap and reproducible.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransactionType, User
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.services import periods
from app.services.schemas import CategoryTotal, PeriodReport


class AnalyticsService:
    """Builds spending reports and digests from stored transactions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._transactions = TransactionRepository(session)
        self._users = UserRepository(session)

    async def period_report(
        self,
        user: User,
        title: str,
        start: datetime,
        end: datetime,
        tx_type: TransactionType = TransactionType.expense,
    ) -> PeriodReport:
        """Build a breakdown of spending by category for ``[start, end)``.

        Percentages are computed against the period total and always sum to
        ~100 (subject to rounding).
        """
        rows = await self._transactions.total_by_category(
            user.id, tx_type, start, end
        )
        total = sum(amount for _, amount in rows)

        category_totals = [
            CategoryTotal(
                name=name,
                total=amount,
                percent=(amount / total * 100.0) if total else 0.0,
            )
            for name, amount in rows
        ]
        return PeriodReport(
            title=title,
            total=total,
            currency=user.currency,
            rows=category_totals,
        )

    async def today(self, user: User) -> PeriodReport:
        start, end = periods.today_range()
        return await self.period_report(user, "Сегодня", start, end)

    async def week(self, user: User) -> PeriodReport:
        start, end = periods.week_range()
        return await self.period_report(user, "Эта неделя", start, end)

    async def month(self, user: User) -> PeriodReport:
        start, end = periods.month_range()
        return await self.period_report(user, "Этот месяц", start, end)

    async def weekly_digest(self, user: User) -> dict[str, object]:
        """Compare this week's spending with last week's.

        Returns a dict with ``current_total``, ``previous_total``,
        ``change_percent`` and ``top`` (the ordered category rows for the
        current week). ``change_percent`` is ``None`` when there is no prior
        spending to compare against.
        """
        cur_start, cur_end = periods.week_range()
        prev_start, prev_end = periods.previous_week_range()

        current_rows = await self._transactions.total_by_category(
            user.id, TransactionType.expense, cur_start, cur_end
        )
        previous_rows = await self._transactions.total_by_category(
            user.id, TransactionType.expense, prev_start, prev_end
        )

        current_total = sum(a for _, a in current_rows)
        previous_total = sum(a for _, a in previous_rows)

        if previous_total > 0:
            change_percent: float | None = (
                (current_total - previous_total) / previous_total * 100.0
            )
        else:
            change_percent = None

        return {
            "current_total": current_total,
            "previous_total": previous_total,
            "change_percent": change_percent,
            "top": current_rows,
            "currency": user.currency,
        }
