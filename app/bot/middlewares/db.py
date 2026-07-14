"""Middleware that injects a fresh async DB session into every handler."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.base import async_session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Open one :class:`AsyncSession` per update, available as ``data['session']``.

    The session is closed automatically after the handler returns. Services
    own commit/rollback; the middleware just guarantees cleanup.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            return await handler(event, data)
