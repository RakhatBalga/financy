"""``/start`` — register the user, ask onboarding questions, show help."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    FOOD_PREFIX,
    HOUSING_PREFIX,
    food_question_keyboard,
    housing_question_keyboard,
    main_reply_keyboard,
)
from app.services.user_service import UserService

router = Router(name="start")

_WELCOME = (
    "👋 Сәлем! Жеке қаржыны есепке алуға көмектесемін.\n\n"
    "Шығынды жай мәтінмен жаз, мысалы:\n"
    "• <i>кофе 800</i>\n"
    "• <i>такси 1500</i>\n"
    "• <i>жалақы 400000</i>\n\n"
    "Командалар:\n"
    "/today · /week · /month — кезең бойынша шығындар\n"
    "/incomes — айлық кіріс пен баланс\n"
    "/chart — айлық шығын диаграммасы\n"
    "/recent — шығындарды өзгерту немесе жою\n"
    "/setbudget &lt;санат&gt; &lt;сома&gt; — айлық лимит\n"
    "/income &lt;сома&gt; — кірісті көрсету\n"
    "/rule — 50/30/20 ережесі\n"
    "/advice — айдың ЖИ талдауы мен кеңестер\n"
    "/profile — кеңестерге арналған қаржылық профиль\n"
    "/benchmark — Қазақстан орташасымен салыстыру\n"
    "/subscriptions — тұрақты төлемдерді табу\n"
    "/portfolio — инвестициялық портфель\n"
    "/deposits — депозиттер\n"
    "/fingoals — қаржылық мақсаттар\n"
    "/capital — барлық капитал USD және KZT түрінде\n"
    "/reset — БАРЛЫҚ шығын, кіріс пен бюджетті жою"
)

_ONBOARDING_INTRO = (
    "Тағы бірнеше сұрақ — бұл кеңестерді дәлірек есептеуге көмектеседі "
    "(мысалы, ата-анаңмен тұрсаң, жалдау ақысын ойдан шығармау үшін)."
)


async def _ask_housing(message: Message) -> None:
    await message.answer(
        _ONBOARDING_INTRO + "\n\nТұрғын үй — оны өзің төлейсің бе, әлде тегін бе?",
        reply_markup=housing_question_keyboard(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    assert message.from_user is not None
    service = UserService(session)
    user, created = await service.register(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )

    prefix = "" if created else "Қайта келуіңізбен!\n\n"
    await message.answer(prefix + _WELCOME, reply_markup=main_reply_keyboard())

    if user.housing_is_free is None:
        await _ask_housing(message)
    elif user.food_is_free is None:
        # Resume: housing was answered in a prior /start but food wasn't yet.
        await message.answer(
            "Ал тамақ — негізінен үйде тегін жейсің бе, әлде тамаққа өзің жұмсайсың ба?",
            reply_markup=food_question_keyboard(),
        )


@router.callback_query(F.data.startswith(f"{HOUSING_PREFIX}:"))
async def on_housing_answer(callback: CallbackQuery, session: AsyncSession) -> None:
    assert callback.data is not None and callback.from_user is not None
    is_free = callback.data.split(":")[1] == "1"

    user = await UserService(session).get(callback.from_user.id)
    if user is None:
        await callback.answer("Алдымен /start басыңыз.", show_alert=True)
        return

    # Commit now (not just flush) — the food answer arrives in a *separate*
    # Telegram update with its own DB session, so this must be durable before
    # then, not just visible within the current session.
    user.housing_is_free = is_free  # type: ignore[assignment]
    await session.commit()

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "Ал тамақ — негізінен үйде тегін жейсің бе, әлде тамаққа өзің жұмсайсың ба?",
            reply_markup=food_question_keyboard(),
        )


@router.callback_query(F.data.startswith(f"{FOOD_PREFIX}:"))
async def on_food_answer(callback: CallbackQuery, session: AsyncSession) -> None:
    assert callback.data is not None and callback.from_user is not None
    food_is_free = callback.data.split(":")[1] == "1"

    user = await UserService(session).get(callback.from_user.id)
    if user is None:
        await callback.answer("Алдымен /start басыңыз.", show_alert=True)
        return

    housing_is_free = bool(user.housing_is_free)
    await UserService(session).set_living_situation(
        user, housing_is_free=housing_is_free, food_is_free=food_is_free
    )

    await callback.answer("Рахмет, мұны кеңестерде ескеремін ✅")
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "Дайын! Шығындарды жай мәтінмен жаза аласың немесе /rule "
            "және 🧠 «ЖИ пікірі» аша аласың — енді кеңестер дәлірек."
        )
