"""Use-case service for user registration."""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import User
from app.repositories.category_repo import CategoryRepository
from app.repositories.user_repo import UserRepository

log = structlog.get_logger(__name__)


class UserService:
    """Registration and lookup of users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._categories = CategoryRepository(session)

    async def register(
        self, telegram_id: int, username: str | None
    ) -> tuple[User, bool]:
        """Return ``(user, created)`` for the given Telegram id.

        On first contact the user row is created together with the default
        set of categories. Idempotent: repeated ``/start`` returns the
        existing user with ``created=False``.
        """
        existing = await self._users.get_by_telegram_id(telegram_id)
        if existing is not None:
            return existing, False

        user = await self._users.create(
            telegram_id=telegram_id,
            username=username,
            currency=settings.default_currency,
        )
        await self._categories.create_defaults(user.id)
        await self._session.commit()

        log.info("user_registered", telegram_id=telegram_id, user_id=user.id)
        return user, True

    async def get(self, telegram_id: int) -> User | None:
        return await self._users.get_by_telegram_id(telegram_id)

    async def set_income(self, user: User, monthly_income: float) -> None:
        """Store the user's monthly income (enables 50/30/20 advice)."""
        if monthly_income <= 0:
            raise ValueError("income must be positive")
        await self._users.set_income(user, monthly_income)
        await self._session.commit()
        log.info("income_set", user_id=user.id)

    async def set_living_situation(
        self, user: User, *, housing_is_free: bool, food_is_free: bool
    ) -> None:
        """Store the onboarding answers (housing/food paid for by the user or not)."""
        await self._users.set_living_situation(
            user, housing_is_free=housing_is_free, food_is_free=food_is_free
        )
        await self._session.commit()
        log.info(
            "living_situation_set",
            user_id=user.id,
            housing_is_free=housing_is_free,
            food_is_free=food_is_free,
        )

    async def set_financial_profile(
        self,
        user: User,
        *,
        age: int,
        debt_balance: float | None,
        debt_annual_rate: float | None,
        risk_tolerance: str | None,
        obligation_type: str | None,
    ) -> None:
        if age < 14 or age > 100:
            raise ValueError("invalid age")
        if debt_balance is not None and debt_balance < 0:
            raise ValueError("invalid debt balance")
        if debt_annual_rate is not None and not 0 <= debt_annual_rate <= 100:
            raise ValueError("invalid debt rate")
        if risk_tolerance not in {None, "низкий", "средний", "высокий"}:
            raise ValueError("invalid risk tolerance")
        if obligation_type not in {None, "кредиты", "рассрочки"}:
            raise ValueError("invalid obligation type")
        await self._users.set_financial_profile(
            user,
            age=age,
            debt_balance=debt_balance,
            debt_annual_rate=debt_annual_rate,
            risk_tolerance=risk_tolerance,
            obligation_type=obligation_type,
        )
        await self._session.commit()
        log.info("financial_profile_set", user_id=user.id)
