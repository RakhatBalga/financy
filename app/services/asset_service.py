"""Use cases and calculations for assets and financial goals."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Deposit, FinancialGoal, InvestmentPosition
from app.repositories.asset_repo import AssetRepository
from app.services.market_data import MarketDataError, YahooFinanceService


SUPPORTED_CURRENCIES = {"KZT", "USD"}


@dataclass(frozen=True)
class PositionValue:
    position: InvestmentPosition
    current_price_usd: float | None
    cost_usd: float
    value_usd: float

    @property
    def profit_usd(self) -> float:
        return self.value_usd - self.cost_usd

    @property
    def profit_percent(self) -> float:
        return self.profit_usd / self.cost_usd * 100 if self.cost_usd else 0


@dataclass(frozen=True)
class WealthSummary:
    positions: list[PositionValue]
    deposits: list[Deposit]
    usd_kzt: float

    @property
    def portfolio_usd(self) -> float:
        return sum(item.value_usd for item in self.positions)

    @property
    def deposits_kzt(self) -> float:
        return sum(
            float(item.balance) * (self.usd_kzt if item.currency == "USD" else 1)
            for item in self.deposits
        )

    @property
    def total_kzt(self) -> float:
        return self.portfolio_usd * self.usd_kzt + self.deposits_kzt

    @property
    def total_usd(self) -> float:
        return self.total_kzt / self.usd_kzt


class AssetService:
    def __init__(
        self, session: AsyncSession, market: YahooFinanceService | None = None
    ) -> None:
        self._session = session
        self._repo = AssetRepository(session)
        self._market = market or YahooFinanceService()

    async def add_position(
        self, user_id: int, symbol: str, quantity: float, average_price_usd: float
    ) -> InvestmentPosition:
        normalized = symbol.strip().upper()
        if not normalized or quantity <= 0 or average_price_usd <= 0:
            raise ValueError("position values must be positive")
        item = await self._repo.add_position(
            user_id, normalized, quantity, average_price_usd
        )
        await self._session.commit()
        return item

    async def add_deposit(
        self,
        user_id: int,
        name: str,
        balance: float,
        currency: str,
        annual_rate: float | None = None,
    ) -> Deposit:
        normalized_currency = currency.upper()
        if (
            not name.strip()
            or balance <= 0
            or normalized_currency not in SUPPORTED_CURRENCIES
            or (annual_rate is not None and annual_rate < 0)
        ):
            raise ValueError("invalid deposit")
        item = await self._repo.add_deposit(
            user_id,
            name.strip(),
            balance,
            normalized_currency,
            annual_rate,
        )
        await self._session.commit()
        return item

    async def add_goal(
        self,
        user_id: int,
        title: str,
        target_amount: float,
        current_amount: float,
        currency: str,
    ) -> FinancialGoal:
        normalized_currency = currency.upper()
        if (
            not title.strip()
            or target_amount <= 0
            or current_amount < 0
            or normalized_currency not in SUPPORTED_CURRENCIES
        ):
            raise ValueError("invalid goal")
        item = await self._repo.add_goal(
            user_id,
            title.strip(),
            target_amount,
            current_amount,
            normalized_currency,
        )
        await self._session.commit()
        return item

    async def update_goal_amount(
        self, user_id: int, goal_id: int, current_amount: float
    ) -> FinancialGoal | None:
        if current_amount < 0:
            return None
        goal = await self._session.get(FinancialGoal, goal_id)
        if goal is None or goal.user_id != user_id:
            return None
        goal.current_amount = current_amount
        await self._session.commit()
        return goal

    async def update_deposit_balance(
        self, user_id: int, deposit_id: int, balance: float
    ) -> Deposit | None:
        if balance < 0:
            return None
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None or deposit.user_id != user_id:
            return None
        deposit.balance = balance
        await self._session.commit()
        return deposit

    async def positions(self, user_id: int) -> list[InvestmentPosition]:
        return await self._repo.list_positions(user_id)

    async def deposits(self, user_id: int) -> list[Deposit]:
        return await self._repo.list_deposits(user_id)

    async def goals(self, user_id: int) -> list[FinancialGoal]:
        return await self._repo.list_goals(user_id)

    async def wealth(self, user_id: int) -> WealthSummary:
        positions = await self.positions(user_id)
        deposits = await self.deposits(user_id)
        usd_kzt = await self._market.usd_kzt()

        async def value_position(position: InvestmentPosition) -> PositionValue:
            cost = float(position.quantity) * float(position.average_price_usd)
            try:
                quote = await self._market.quote(position.symbol)
                if quote.currency != "USD":
                    raise MarketDataError("only USD stock quotes are supported")
                current_price = quote.price
                value = float(position.quantity) * current_price
            except MarketDataError:
                current_price = None
                value = cost
            return PositionValue(position, current_price, cost, value)

        values = list(
            await asyncio.gather(*(value_position(item) for item in positions))
        )
        return WealthSummary(values, deposits, usd_kzt)

    async def delete_position(self, user_id: int, item_id: int) -> bool:
        return await self._repo.delete_owned(InvestmentPosition, user_id, item_id)

    async def delete_deposit(self, user_id: int, item_id: int) -> bool:
        return await self._repo.delete_owned(Deposit, user_id, item_id)

    async def delete_goal(self, user_id: int, item_id: int) -> bool:
        return await self._repo.delete_owned(FinancialGoal, user_id, item_id)
