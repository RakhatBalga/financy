"""``/income <amount>`` — set monthly income for the 50/30/20 advice."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatters import format_amount
from app.services.user_service import UserService

router = Router(name="income")

_USAGE = (
    "Использование: <code>/income &lt;сумма&gt;</code>\n"
    "Например: <code>/income 400000</code>"
)


@router.message(Command("income"))
async def cmd_income(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    assert message.from_user is not None

    service = UserService(session)
    user = await service.get(message.from_user.id)
    if user is None:
        await message.answer("Сначала выполни /start.")
        return

    if not command.args:
        current = (
            format_amount(float(user.monthly_income), user.currency)
            if user.monthly_income
            else "не задан"
        )
        await message.answer(f"Текущий доход: {current}\n\n{_USAGE}")
        return

    try:
        amount = float(command.args.replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом.\n\n" + _USAGE)
        return

    try:
        await service.set_income(user, amount)
    except ValueError:
        await message.answer("Доход должен быть больше нуля.")
        return

    await message.answer(
        f"✅ Месячный доход сохранён: {format_amount(amount, user.currency)}\n"
        "Теперь доступна команда /rule (правило 50/30/20)."
    )
