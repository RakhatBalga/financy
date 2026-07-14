"""Reference spending structure for Kazakhstan (shares of expenses, %).

Approximate shares of household consumption expenditure by category, based on
the Bureau of National Statistics household budget survey (stat.gov.kz). These
are *shares of total spending*, not absolute amounts — comparing shares is fair
across different income levels, unlike comparing tenge figures.

Update roughly once a year from the latest published survey. Numbers here are
rounded, illustrative reference points — not exact official figures.
"""

from __future__ import annotations

# category name -> approximate share of total household spending (%)
KZ_EXPENSE_SHARES: dict[str, float] = {
    "Еда": 45.0,
    "Жильё": 15.0,
    "Транспорт": 12.0,
    "Здоровье": 8.0,
    "Развлечения": 7.0,
    "Другое": 13.0,
}


def compare_shares(
    user_shares: dict[str, float],
) -> list[tuple[str, float, float]]:
    """Compare a user's category shares against the KZ reference.

    ``user_shares`` maps category name -> percent of the user's spending.
    Returns ``[(category, user_pct, kz_pct), ...]`` only for categories that
    exist in the reference, ordered by the size of the gap (user − kz) so the
    biggest deviations come first.
    """
    rows: list[tuple[str, float, float]] = []
    for name, kz_pct in KZ_EXPENSE_SHARES.items():
        user_pct = user_shares.get(name, 0.0)
        rows.append((name, user_pct, kz_pct))
    rows.sort(key=lambda r: abs(r[1] - r[2]), reverse=True)
    return rows
