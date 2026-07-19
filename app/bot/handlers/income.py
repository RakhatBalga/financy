"""``/income`` — set monthly income for the 50/30/20 advice.

Works two ways:
* ``/income 400000`` — sets it directly.
* ``/income`` alone — bot asks for the amount and the next number is stored
  (FSM waiting state), so replying with just ``125000`` works as expected.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatters import format_amount
from app.bot.keyboards import MENU_BUTTONS
from app.db.models import User
from app.services.user_service import UserService

router = Router(name="income")


class IncomeStates(StatesGroup):
    """Waiting for the user to type their monthly income."""

    waiting = State()


def _parse_amount(raw: str) -> float | None:
    try:
        return float(raw.replace(" ", "").replace(",", "."))
    except ValueError:
        return None


async def _apply_income(
    message: Message, session: AsyncSession, user: User, amount: float
) -> None:
    try:
        await UserService(session).set_income(user, amount)
    except ValueError:
        await message.answer("Кіріс нөлден үлкен болуы керек.")
        return
    await message.answer(
        f"✅ Күтілетін кіріс сақталды: {format_amount(amount, user.currency)}\n"
        "Бұл baseline — соманы шын өзгергенде ғана жаңарт, "
        "әр ай сайын емес. Ақша түскенде жай жаз "
        "<i>жалақы 150000</i> — ереже нақты түсімдерді ескереді.\n"
        "/rule (50/30/20 ережесі) қара."
    )


@router.message(Command("income"))
async def cmd_income(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    assert message.from_user is not None

    user = await UserService(session).get(message.from_user.id)
    if user is None:
        await message.answer("Алдымен /start басыңыз.")
        return

    if not command.args:
        current = (
            format_amount(float(user.monthly_income), user.currency)
            if user.monthly_income
            else "қойылмаған"
        )
        await state.set_state(IncomeStates.waiting)
        await message.answer(
            f"Ағымдағы кіріс: {current}\n\n"
            "Айлық кірісті санмен енгіз (мысалы 400000):"
        )
        return

    amount = _parse_amount(command.args)
    if amount is None:
        await message.answer("Сома сан болуы керек. Мысалы: /income 400000")
        return
    await _apply_income(message, session, user, amount)


@router.message(
    IncomeStates.waiting,
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_(MENU_BUTTONS),
)
async def on_income_amount(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    assert message.from_user is not None and message.text is not None

    amount = _parse_amount(message.text)
    if amount is None:
        # Not a number — abandon the input rather than trapping the user.
        await state.clear()
        await message.answer(
            "Бұл сомаға ұқсамайды — кіріс енгізуді болдырмадым. "
            "Былай қоюға болады: <code>/income 400000</code>."
        )
        return

    await state.clear()
    user = await UserService(session).get(message.from_user.id)
    if user is None:
        await message.answer("Алдымен /start басыңыз.")
        return
    await _apply_income(message, session, user, amount)
