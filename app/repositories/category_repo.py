"""Data access for :class:`Category`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category

# Default categories mapped to their 50/30/20 bucket. Income is tracked by
# transaction type, not category group, so no "income" bucket is needed here.
DEFAULT_CATEGORY_GROUPS: dict[str, str] = {
    "Еда": "needs",
    "Транспорт": "needs",
    "Жильё": "needs",
    "Развлечения": "wants",
    "Здоровье": "needs",
    "Другое": "wants",
}
DEFAULT_CATEGORIES: tuple[str, ...] = tuple(DEFAULT_CATEGORY_GROUPS)


class CategoryRepository:
    """CRUD operations for categories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_defaults(self, user_id: int) -> list[Category]:
        """Create the default category set for a freshly-registered user."""
        categories = [
            Category(
                user_id=user_id,
                name=name,
                is_default=True,
                group_type=group,
            )
            for name, group in DEFAULT_CATEGORY_GROUPS.items()
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
        """Case-insensitive lookup of a category by name.

        Matching is done in Python with ``casefold`` rather than SQL
        ``lower()`` — SQLite's ``lower()`` does not fold non-ASCII (Cyrillic)
        letters, which would silently break lookups and create duplicates.
        A user has only a handful of categories, so loading them is cheap.
        """
        target = name.strip().casefold()
        for category in await self.list_for_user(user_id):
            if category.name.casefold() == target:
                return category
        return None

    async def get_or_create(self, user_id: int, name: str) -> Category:
        """Return an existing category by name or create a custom one.

        Custom categories default to the "wants" bucket for 50/30/20.
        """
        existing = await self.get_by_name(user_id, name)
        if existing is not None:
            return existing
        category = Category(
            user_id=user_id, name=name, is_default=False, group_type="wants"
        )
        self._session.add(category)
        await self._session.flush()
        return category
