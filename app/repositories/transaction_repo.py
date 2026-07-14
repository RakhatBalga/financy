"""Data access for :class:`Transaction`."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Transaction, TransactionType


class TransactionRepository:
    """CRUD and aggregation queries for transactions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        category_id: int,
        amount: float,
        tx_type: TransactionType,
        description: str | None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=tx_type,
            description=description,
        )
        self._session.add(transaction)
        await self._session.flush()
        return transaction

    async def total_by_category(
        self,
        user_id: int,
        tx_type: TransactionType,
        start: datetime,
        end: datetime,
    ) -> list[tuple[str, float]]:
        """Sum amounts grouped by category name for a period ``[start, end)``.

        Returns ``[(category_name, total), ...]`` ordered by total descending.
        """
        stmt = (
            select(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == tx_type,
                Transaction.created_at >= start,
                Transaction.created_at < end,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
        result = await self._session.execute(stmt)
        return [(name, float(total)) for name, total in result.all()]

    async def total_for_category(
        self,
        user_id: int,
        category_id: int,
        tx_type: TransactionType,
        start: datetime,
        end: datetime,
    ) -> float:
        """Total amount for a single category in a period ``[start, end)``."""
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == tx_type,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        result = await self._session.execute(stmt)
        return float(result.scalar_one())
