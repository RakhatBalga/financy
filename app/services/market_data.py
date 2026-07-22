"""Small async Yahoo Finance client for stock prices and USD/KZT."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class MarketDataError(RuntimeError):
    """Raised when Yahoo Finance has no usable quote."""


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    price: float
    currency: str
    name: str


class YahooFinanceService:
    """Fetch Yahoo chart metadata and cache it briefly in process."""

    def __init__(self, cache_seconds: int = 300) -> None:
        self._cache_seconds = cache_seconds
        self._cache: dict[str, tuple[float, MarketQuote]] = {}

    async def quote(self, symbol: str) -> MarketQuote:
        normalized = symbol.strip().upper()
        cached = self._cache.get(normalized)
        now = time.monotonic()
        if cached is not None and now - cached[0] < self._cache_seconds:
            return cached[1]

        result = await asyncio.to_thread(self._fetch, normalized)
        self._cache[normalized] = (now, result)
        return result

    async def usd_kzt(self) -> float:
        return (await self.quote("USDKZT=X")).price

    @staticmethod
    def _fetch(symbol: str) -> MarketQuote:
        encoded = quote(symbol, safe="")
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
            "?interval=1d&range=1d"
        )
        request = Request(url, headers={"User-Agent": "FincancyBot/1.0"})
        try:
            with urlopen(request, timeout=8) as response:  # noqa: S310 - fixed host
                payload = json.load(response)
            result = payload["chart"]["result"][0]
            meta = result["meta"]
            price = float(meta["regularMarketPrice"])
            if price <= 0:
                raise ValueError("non-positive price")
            return MarketQuote(
                symbol=str(meta.get("symbol") or symbol).upper(),
                price=price,
                currency=str(meta.get("currency") or "USD").upper(),
                name=str(meta.get("shortName") or meta.get("longName") or symbol),
            )
        except (
            HTTPError,
            URLError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as exc:
            raise MarketDataError(f"quote unavailable for {symbol}") from exc
