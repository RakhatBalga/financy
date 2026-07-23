"""Data access for :class:`User`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    """CRUD operations for users. All methods are async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Return the user with the given Telegram id, or ``None``."""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, telegram_id: int, username: str | None, currency: str
    ) -> User:
        """Insert a new user and flush so its ``id`` is populated."""
        user = User(telegram_id=telegram_id, username=username, currency=currency)
        self._session.add(user)
        await self._session.flush()
        return user

    async def list_all(self) -> list[User]:
        """Return every user (used by scheduled jobs)."""
        result = await self._session.execute(select(User))
        return list(result.scalars().all())

    async def set_income(self, user: User, monthly_income: float) -> None:
        """Persist the user's declared monthly income."""
        user.monthly_income = monthly_income
        await self._session.flush()

    async def set_living_situation(
        self, user: User, *, housing_is_free: bool, food_is_free: bool
    ) -> None:
        """Persist the onboarding answers about housing/food costs."""
        user.housing_is_free = housing_is_free
        user.food_is_free = food_is_free
        await self._session.flush()

    async def set_financial_profile(
        self,
        user: User,
        *,
        age: int,
        debt_balance: float | None,
        debt_annual_rate: float | None,
        risk_tolerance: str | None,
    ) -> None:
        user.age = age
        user.debt_balance = debt_balance
        user.debt_annual_rate = debt_annual_rate
        user.risk_tolerance = risk_tolerance
        await self._session.flush()
