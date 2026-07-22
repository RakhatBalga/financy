"""Tests for portfolio, deposit, and goal calculations."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.asset_service import AssetService
from app.services.market_data import MarketDataError, MarketQuote


class FakeMarket:
    async def usd_kzt(self) -> float:
        return 500.0

    async def quote(self, symbol: str) -> MarketQuote:
        if symbol == "MISSING":
            raise MarketDataError("missing")
        return MarketQuote(symbol, 120.0, "USD", symbol)


async def test_wealth_combines_stocks_and_deposits(
    session: AsyncSession, user: User
) -> None:
    service = AssetService(session, FakeMarket())  # type: ignore[arg-type]
    await service.add_position(user.id, "aapl", 2, 100)
    await service.add_deposit(user.id, "Kaspi", 100_000, "KZT", 15)

    summary = await service.wealth(user.id)

    assert summary.portfolio_usd == pytest.approx(240)
    assert summary.deposits_kzt == pytest.approx(100_000)
    assert summary.total_kzt == pytest.approx(220_000)
    assert summary.total_usd == pytest.approx(440)
    assert summary.positions[0].profit_usd == pytest.approx(40)
    assert summary.positions[0].profit_percent == pytest.approx(20)


async def test_missing_quote_uses_cost_basis_without_losing_position(
    session: AsyncSession, user: User
) -> None:
    service = AssetService(session, FakeMarket())  # type: ignore[arg-type]
    await service.add_position(user.id, "MISSING", 3, 50)

    summary = await service.wealth(user.id)

    assert summary.positions[0].current_price_usd is None
    assert summary.positions[0].value_usd == pytest.approx(150)


async def test_goal_can_be_updated_and_deleted(
    session: AsyncSession, user: User
) -> None:
    service = AssetService(session, FakeMarket())  # type: ignore[arg-type]
    goal = await service.add_goal(user.id, "MacBook", 1_500_000, 300_000, "kzt")

    updated = await service.update_goal_amount(user.id, goal.id, 450_000)
    assert updated is not None
    assert float(updated.current_amount) == pytest.approx(450_000)

    assert await service.delete_goal(user.id, goal.id)
    assert await service.goals(user.id) == []


async def test_deposit_balance_can_be_updated(
    session: AsyncSession, user: User
) -> None:
    service = AssetService(session, FakeMarket())  # type: ignore[arg-type]
    deposit = await service.add_deposit(user.id, "Kaspi", 100_000, "KZT")

    updated = await service.update_deposit_balance(user.id, deposit.id, 125_000)

    assert updated is not None
    assert float(updated.balance) == pytest.approx(125_000)
