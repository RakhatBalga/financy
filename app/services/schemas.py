"""Pydantic DTOs shared across the service layer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.db.models import TransactionType


class ParsedTransaction(BaseModel):
    """Structured result of parsing a free-text expense/income message.

    This schema is also handed to Gemini as the ``response_schema`` for
    controlled generation, so the model is forced to emit exactly these
    fields as valid JSON.
    """

    amount: float = Field(description="Positive amount of money, e.g. 800.0")
    category: str = Field(description="Best-matching category name")
    type: TransactionType = Field(description="Either 'expense' or 'income'")
    description: str = Field(description="Short human description of the item")


class CategoryTotal(BaseModel):
    """One row of a period breakdown."""

    name: str
    total: float
    percent: float


class PeriodReport(BaseModel):
    """Aggregated spending report for a period."""

    title: str
    total: float
    currency: str
    rows: list[CategoryTotal]
