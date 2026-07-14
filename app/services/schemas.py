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

    amount: float = Field(description="Positive amount in KZT, e.g. 800.0")
    type: TransactionType = Field(description="Either 'expense' or 'income'")
    category: str = Field(description="Lowercase category name")
    description: str = Field(description="1-4 word description, no amount")
    confidence: str = Field(
        default="high", description="'high' if unambiguous, else 'low'"
    )


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
