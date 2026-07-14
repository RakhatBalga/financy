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

    Category names live in a legend on the right (with their percent), so no
    text overlaps the pie itself. Returns ``None`` when there is nothing to plot.
    """
    if not report.rows:
        return None

    values = [r.total for r in report.rows]
    percents = [r.percent for r in report.rows]
    colors = [_COLORS[i % len(_COLORS)] for i in range(len(values))]

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=120)
    wedges, _texts = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
    )
    ax.axis("equal")

    ax.set_title(
        f"{report.title}: {report.total:,.0f} {report.currency}".replace(",", " "),
        fontsize=15,
        fontweight="bold",
        loc="left",
        pad=18,
    )

    # Legend on the right: "Категория — 51%", biggest first (rows are sorted).
    legend_labels = [
        f"{r.name}  —  {p:.0f}%" for r, p in zip(report.rows, percents)
    ]
    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=12,
        handlelength=1.2,
        labelspacing=0.8,
    )

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()
