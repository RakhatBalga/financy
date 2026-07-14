"""Render spending breakdowns to PNG images with matplotlib.

Uses the non-interactive Agg backend (no display needed inside the container).
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")  # must be set before importing pyplot

import matplotlib.pyplot as plt  # noqa: E402

from app.services.schemas import PeriodReport  # noqa: E402

# Brand-ish palette; cycles if there are more categories than colors.
_COLORS = [
    "#2563EB", "#0EA5E9", "#14B8A6", "#F59E0B",
    "#EF4444", "#8B5CF6", "#EC4899", "#84CC16",
]


def pie_chart(report: PeriodReport) -> bytes | None:
    """Render a category pie chart for ``report`` and return PNG bytes.

    Returns ``None`` when there is nothing to plot.
    """
    if not report.rows:
        return None

    labels = [r.name for r in report.rows]
    values = [r.total for r in report.rows]
    colors = [_COLORS[i % len(_COLORS)] for i in range(len(values))]

    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    wedges, _texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct=lambda pct: f"{pct:.0f}%",
        startangle=90,
        pctdistance=0.78,
        textprops={"fontsize": 11},
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontweight("bold")

    ax.set_title(
        f"{report.title}: {report.total:,.0f} {report.currency}".replace(",", " "),
        fontsize=14,
        fontweight="bold",
        pad=16,
    )
    ax.axis("equal")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()
