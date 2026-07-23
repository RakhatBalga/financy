"""Formatting helpers for the user's installment payment schedule."""

from __future__ import annotations

from datetime import date

from app.db.models import User


def _month(entry: dict[str, int]) -> date:
    return date.fromisoformat(f"{entry['month']}-01")


def _label(start: date, end: date) -> str:
    if start == end:
        return start.strftime("%m.%Y")
    if start.year == end.year:
        return f"{start:%m}–{end:%m.%Y}"
    return f"{start:%m.%Y}–{end:%m.%Y}"


def installment_schedule_summary(user: User, *, combined: bool) -> str | None:
    """Collapse consecutive equal payments into a readable timeline."""
    schedule = user.installment_kaspi_schedule or []
    if not schedule:
        return None

    halyk_payment = float(user.installment_halyk_monthly_payment or 0)
    halyk_end = user.installment_halyk_end_date
    rows: list[tuple[date, float]] = []
    for entry in schedule:
        month = _month(entry)
        payment = float(entry["amount"])
        if combined and halyk_end and month <= halyk_end.replace(day=1):
            payment += halyk_payment
        rows.append((month, payment))
    rows.sort(key=lambda row: row[0])

    ranges: list[tuple[date, date, float]] = []
    for month, payment in rows:
        if ranges:
            start, end, previous_payment = ranges[-1]
            next_year = end.year + (end.month == 12)
            next_month = 1 if end.month == 12 else end.month + 1
            if month == date(next_year, next_month, 1) and payment == previous_payment:
                ranges[-1] = (start, month, payment)
                continue
        ranges.append((month, month, payment))

    return "; ".join(
        f"{_label(start, end)} — {payment:,.0f} ₸".replace(",", " ")
        for start, end, payment in ranges
    )
