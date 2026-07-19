"""``/subscriptions`` — detect recurring payments from history."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatters import format_subscriptions
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService

router = Router(name="subscriptions")


@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message, session: AsyncSession) -> None:
    assert message.from_user is not None
    user = await UserService(session).get(message.from_user.id)
    if user is None:
        await message.answer("Алдымен /start басыңыз.")
        return
    subs = await AnalyticsService(session).detect_subscriptions(user)
    await message.answer(format_subscriptions(subs, user.currency))
