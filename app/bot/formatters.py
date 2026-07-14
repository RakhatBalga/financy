"""Render domain objects into Telegram-ready text tables."""

from __future__ import annotations

from app.services.budget_service import BudgetAlert
from app.services.schemas import ParsedTransaction, PeriodReport


def format_amount(value: float, currency: str) -> str:
    """Format money with a thin space thousands separator."""
    return f"{value:,.0f}".replace(",", " ") + f" {currency}"


def format_confirmation(parsed: ParsedTransaction, currency: str) -> str:
    kind = "Доход" if parsed.type.value == "income" else "Расход"
    return (
        f"<b>{kind}</b>\n"
        f"Сумма: {format_amount(parsed.amount, currency)}\n"
        f"Категория: {parsed.category}\n"
        f"Описание: {parsed.description}"
    )


def format_period_report(report: PeriodReport) -> str:
    """Render a :class:`PeriodReport` as a monospace text table."""
    if not report.rows:
        return f"<b>{report.title}</b>\nПока нет трат за этот период."

    lines = [
        f"<b>{report.title}</b>",
        f"Всего: {format_amount(report.total, report.currency)}",
        "",
        "<pre>",
        f"{'Категория':<14}{'Сумма':>12}{'%':>6}",
    ]
    for row in report.rows:
        amount = f"{row.total:,.0f}".replace(",", " ")
        lines.append(f"{row.name[:14]:<14}{amount:>12}{row.percent:>5.0f}%")
    lines.append("</pre>")
    return "\n".join(lines)


def format_budget_alert(alert: BudgetAlert, currency: str) -> str:
    icon = "🚨" if alert.level == "exceeded" else "⚠️"
    verb = "превышен" if alert.level == "exceeded" else "почти исчерпан"
    return (
        f"{icon} Бюджет {verb}: <b>{alert.category_name}</b>\n"
        f"Потрачено {format_amount(alert.spent, currency)} "
        f"из {format_amount(alert.limit, currency)} "
        f"({alert.ratio * 100:.0f}%)"
    )


def format_weekly_digest(digest: dict[str, object]) -> str:
    """Render the weekly comparison digest."""
    currency = str(digest["currency"])
    current = float(digest["current_total"])  # type: ignore[arg-type]
    change = digest["change_percent"]
    top = digest["top"]  # list[tuple[str, float]]

    lines = [
        "🗓 <b>Итоги недели</b>",
        f"Потрачено: {format_amount(current, currency)}",
    ]
    if change is None:
        lines.append("Сравнить не с чем — это первая неделя с тратами.")
    else:
        change_f = float(change)
        arrow = "🔺" if change_f > 0 else ("🔻" if change_f < 0 else "▪️")
        lines.append(f"К прошлой неделе: {arrow} {abs(change_f):.0f}%")

    if top:
        lines.append("\nТоп категорий:")
        for name, amount in list(top)[:5]:  # type: ignore[arg-type]
            lines.append(f"• {name}: {format_amount(float(amount), currency)}")
    return "\n".join(lines)
