"""Pytest fixtures: in-memory SQLite session and seeded user/categories.

Environment defaults are set *before* importing app modules, because
``app.core.config.Settings`` requires ``BOT_TOKEN`` at import time.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("TZ", "UTC")

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db import models  # noqa: F401  (register tables on metadata)
from app.db.base import Base
from app.db.models import User
from app.repositories.category_repo import CategoryRepository


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Fresh in-memory database per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session

    await engine.dispose()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    """A registered user with the default category set."""
    user = User(telegram_id=42, username="tester", currency="KZT")
    session.add(user)
    await session.flush()
    await CategoryRepository(session).create_defaults(user.id)
    await session.commit()
    return user
