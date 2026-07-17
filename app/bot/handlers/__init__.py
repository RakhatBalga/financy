"""Handler routers, aggregated for one-call registration."""

from __future__ import annotations

from aiogram import Router

from app.bot.handlers import (
    advice,
    budget,
    chart,
    income,
    incomes,
    manage,
    reports,
    start,
    subscriptions,
    transactions,
)


def build_router() -> Router:
    """Combine all feature routers into a single root router.

    Order matters: command routers and the FSM-driven ``manage`` router come
    first; the free-text transaction handler is registered last so it only
    catches messages no other handler claimed.
    """
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(reports.router)
    root.include_router(incomes.router)
    root.include_router(budget.router)
    root.include_router(income.router)
    root.include_router(advice.router)
    root.include_router(subscriptions.router)
    root.include_router(chart.router)
    root.include_router(manage.router)  # FSM text handler — before catch-all
    root.include_router(transactions.router)
    return root
