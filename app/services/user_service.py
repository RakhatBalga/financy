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
