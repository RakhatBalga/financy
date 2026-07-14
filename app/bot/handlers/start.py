"""``/start`` — register the user and create default categories."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_reply_keyboard
from app.services.user_service import UserService

router = Router(name="start")

_WELCOME = (
    "👋 Привет! Я помогу вести учёт личных финансов.\n\n"
    "Просто напиши трату обычным текстом, например:\n"
    "• <i>кофе 800</i>\n"
    "• <i>такси 1500</i>\n"
    "• <i>зарплата 400000</i>\n\n"
    "Команды:\n"
    "/today · /week · /month — отчёты за период\n"
    "/chart — график расходов за месяц\n"
    "/recent — изменить или удалить траты\n"
    "/setbudget &lt;категория&gt; &lt;сумма&gt; — лимит на месяц\n"
    "/income &lt;сумма&gt; — указать доход\n"
    "/rule — правило 50/30/20\n"
    "/advice — AI-разбор месяца и советы\n"
    "/benchmark — сравнение со средним по Казахстану\n"
    "/subscriptions — найти регулярные платежи"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    assert message.from_user is not None
    service = UserService(session)
    _, created = await service.register(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    prefix = "" if created else "С возвращением!\n\n"
    await message.answer(prefix + _WELCOME, reply_markup=main_reply_keyboard())
