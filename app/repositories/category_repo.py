"""Data access for :class:`Category`."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category

DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Еда",
    "Транспорт",
    "Жильё",
    "Развлечения",
    "Здоровье",
    "Другое",
)


class CategoryRepository:
    """CRUD operations for categories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_defaults(self, user_id: int) -> list[Category]:
        """Create the default category set for a freshly-registered user."""
        categories = [
            Category(user_id=user_id, name=name, is_default=True)
            for name in DEFAULT_CATEGORIES
        ]
        self._session.add_all(categories)
        await self._session.flush()
        return categories

    async def list_for_user(self, user_id: int) -> list[Category]:
        result = await self._session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int, user_id: int) -> Category | None:
        result = await self._session.execute(
            select(Category).where(
                Category.id == category_id, Category.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: int, name: str) -> Category | None:
        """Case-insensitive lookup of a category by name."""
        result = await self._session.execute(
            select(Category).where(
                Category.user_id == user_id,
                func.lower(Category.name) == name.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int, name: str) -> Category:
        """Return an existing category by name or create a custom one."""
        existing = await self.get_by_name(user_id, name)
        if existing is not None:
            return existing
        category = Category(user_id=user_id, name=name, is_default=False)
        self._session.add(category)
        await self._session.flush()
        return category
