"""Bot and Dispatcher construction with middleware and shared services."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import build_router
from app.bot.middlewares.db import DbSessionMiddleware
from app.core.config import settings
from app.services.parser_service import ParserService


def create_bot() -> Bot:
    """Instantiate the Bot with HTML parse mode as the global default."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Build the Dispatcher: Redis FSM storage, DB middleware, routers.

    The :class:`ParserService` is created once and injected into every handler
    via workflow data (``parser=...``), so the Gemini client is reused.
    """
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Shared singletons available to handlers by parameter name.
    dp["parser"] = ParserService()

    # DB session per update, for both messages and callbacks.
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(build_router())
    return dp
