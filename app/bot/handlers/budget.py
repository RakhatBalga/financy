"""``/setbudget <category> <amount>`` — set a monthly per-category limit."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatters import format_amount
from app.services.budget_service import BudgetService
from app.services.user_service import UserService

router = Router(name="budget")

_USAGE = (
    "Қолдану: <code>/setbudget &lt;санат&gt; &lt;сома&gt;</code>\n"
    "Мысалы: <code>/setbudget азық-түлік 120000</code>"
)


@router.message(Command("setbudget"))
async def cmd_setbudget(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    assert message.from_user is not None

    user = await UserService(session).get(message.from_user.id)
    if user is None:
        await message.answer("Алдымен /start басыңыз.")
        return

    if not command.args:
        await message.answer(_USAGE)
        return

    # Last token is the amount; everything before it is the category name.
    parts = command.args.rsplit(maxsplit=1)
    if len(parts) != 2:
        await message.answer(_USAGE)
        return

    category_name, raw_amount = parts
    try:
        amount = float(raw_amount.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("Сома сан болуы керек.\n\n" + _USAGE)
        return

    try:
        resolved = await BudgetService(session).set_budget(
            user_id=user.id,
            category_name=category_name.strip(),
            monthly_limit=amount,
        )
    except ValueError:
        await message.answer("Сома нөлден үлкен болуы керек.")
        return

    await message.answer(
        f"✅ «{resolved}» үшін айлық лимит қойылды: "
        f"{format_amount(amount, user.currency)}"
    )
