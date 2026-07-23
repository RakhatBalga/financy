"""Tests for the personal context used by financial advice."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.advice import _profile_input, _profile_text
from app.db.models import User
from app.services.user_service import UserService


def test_profile_input_accepts_age_only_and_full_profile() -> None:
    assert _profile_input("21") == (21, None, None, None, None)
    assert _profile_input("21 | 3 500 000 | 19,5 | средний | рассрочки") == (
        21,
        3_500_000,
        19.5,
        "средний",
        "рассрочки",
    )
    assert _profile_input("21 | - | - | -") == (21, None, None, None, None)


def test_profile_input_rejects_unknown_risk() -> None:
    with pytest.raises(ValueError):
        _profile_input("21 | 100000 | 10 | огромный")


async def test_financial_profile_is_persisted(
    session: AsyncSession,
    user: User,
) -> None:
    await UserService(session).set_financial_profile(
        user,
        age=21,
        debt_balance=3_500_000,
        debt_annual_rate=19.5,
        risk_tolerance="средний",
        obligation_type="рассрочки",
    )

    await session.refresh(user)

    assert user.age == 21
    assert float(user.debt_balance or 0) == pytest.approx(3_500_000)
    assert float(user.debt_annual_rate or 0) == pytest.approx(19.5)
    assert user.risk_tolerance == "средний"
    assert user.obligation_type == "рассрочки"


def test_profile_text_shows_official_income_and_installments() -> None:
    user = User(
        telegram_id=42,
        currency="KZT",
        official_salary_monthly=125_000,
        official_stipend_monthly=52_000,
        mortgage_payment_limit_percent=50,
        installment_balance_primary=517_000,
        installment_balance_secondary=356_000,
        installment_end_date=date(2027, 8, 31),
    )

    text = _profile_text(user)

    assert "Официальный доход: 177 000 ₸" in text
    assert "Лимит ипотечного платежа: 88 500 ₸ (50%)" in text
    assert "Остаток рассрочек: 873 000 ₸ · до 08.2027" in text
