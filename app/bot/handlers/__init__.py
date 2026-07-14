"""Handler routers, aggregated for one-call registration."""

from __future__ import annotations

from aiogram import Router

from app.bot.handlers import budget, reports, start, transactions


def build_router() -> Router:
    """Combine all feature routers into a single root router."""
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(reports.router)
    root.include_router(budget.router)
    # Free-text handler goes last so commands are matched first.
    root.include_router(transactions.router)
    return root
