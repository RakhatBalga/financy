"""Coaching layer: 50/30/20 rule + AI-generated monthly advice.

The rule math is pure and deterministic; the AI call turns the numbers (plus
anomalies and subscriptions) into a few concrete, human recommendations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransactionType, User
from app.repositories.transaction_repo import TransactionRepository
from app.services import benchmarks, gemini, periods
from app.services.analytics_service import AnalyticsService

log = structlog.get_logger(__name__)

# Target shares of income for the 50/30/20 rule.
TARGET_NEEDS = 0.50
TARGET_WANTS = 0.30
TARGET_SAVINGS = 0.20


@dataclass(slots=True)
class RuleBreakdown:
    """Result of the 50/30/20 evaluation for the current month."""

    income: float
    needs: float
    wants: float
    savings: float  # income − expenses (can be negative)
    needs_pct: float
    wants_pct: float
    savings_pct: float
    # True if `income` is the sum of income actually logged this month;
    # False if it fell back to the declared /income baseline.
    income_is_actual: bool


_ADVICE_SYSTEM = """
Ты — внимательный финансовый коуч для пользователя из Казахстана. На вход —
подробная сводка за месяц (доходы по источникам, расходы по категориям с долями,
баланс, правило 50/30/20, аномалии, подписки, сравнение со средним по РК).

Дай РАЗВЁРНУТЫЙ разбор на русском в таком формате (используй HTML-теги
<b>...</b> для заголовков, без markdown):

<b>Итог</b>
2-3 предложения: доход, расходы, баланс. Честная и спокойная оценка ситуации.

<b>Что важно</b>
4-6 конкретных рекомендаций, каждая с новой строки начинается с "• ".
В каждой — конкретная категория и сумма из сводки, и что именно сделать.
Сортируй по важности: сначала самое влияющее на баланс.

<b>Следующий шаг</b>
Одно конкретное действие на этот месяц, с ориентиром в тенге.

Правила:
- Опирайся ТОЛЬКО на цифры из сводки, ничего не выдумывай. Валюта — тенге (₸).
- "помощь семье" и "кредиты и рассрочка" — это ОБЯЗАТЕЛЬСТВА, не хотелки.
  НЕ предлагай сократить помощь родным или перестать платить долг.
- Для долгов уместны: рефинансирование/объединение рассрочек, досрочное
  закрытие самой дорогой, план погашения.
- Экономию ищи в дискреционных тратах: еда вне дома, развлечения, подписки,
  такси, одежда, подарки.
- Если обязательные траты превышают доход — скажи честно и спокойно, предложи
  реалистичные шаги, включая дополнительный доход. Без чувства вины и морализаторства.
""".strip()


def _clean_markup(text: str) -> str:
    """Normalise the model's output to Telegram-HTML-friendly markup.

    Converts markdown bold to ``<b>`` and unifies bullet markers to "• ".
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?m)^[ \t]*[*\-•][ \t]+", "• ", text)
    return text.strip()


class AdvisorService:
    """Builds the 50/30/20 breakdown and the monthly AI advice."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._transactions = TransactionRepository(session)
        self._analytics = AnalyticsService(session)

    async def fifty_thirty_twenty(self, user: User) -> RuleBreakdown | None:
        """Evaluate the 50/30/20 rule for this month.

        Income is taken from the actual income transactions logged this month;
        if none yet, it falls back to the declared ``/income`` baseline. So the
        rule updates itself as salary/stipend land — no monthly re-entry needed.
        Returns ``None`` if there is neither logged income nor a baseline.
        """
        start, end = periods.month_range()
        actual_income = await self._transactions.total_amount(
            user.id, TransactionType.income, start, end
        )
        baseline = float(user.monthly_income or 0.0)

        # Use the larger of the two: a small logged gift shouldn't override the
        # expected salary, but real income above the baseline should win.
        income = max(actual_income, baseline)
        income_is_actual = actual_income > 0 and actual_income >= baseline
        if income <= 0:
            return None

        groups = await self._analytics.group_totals(user)
        needs = groups.get("needs", 0.0)
        wants = groups.get("wants", 0.0)
        savings = income - (needs + wants)

        return RuleBreakdown(
            income=income,
            needs=needs,
            wants=wants,
            savings=savings,
            needs_pct=needs / income * 100.0,
            wants_pct=wants / income * 100.0,
            savings_pct=savings / income * 100.0,
            income_is_actual=income_is_actual,
        )

    async def monthly_advice(self, user: User) -> str:
        """Generate a detailed month review from this month's data (AI)."""
        summary = await self._build_summary(user)
        if summary is None:
            return "Пока мало данных за месяц — запиши несколько трат, и я дам совет."

        advice = await gemini.generate_text(summary, _ADVICE_SYSTEM)
        log.info("monthly_advice_generated", user_id=user.id)
        if not advice:
            return "Не получилось сформировать совет, попробуй позже."
        return _clean_markup(advice)

    async def _build_summary(self, user: User) -> str | None:
        """Assemble a compact plain-text summary fed to the model."""
        start, end = periods.month_range()
        rows = await self._transactions.total_by_category(
            user.id, TransactionType.expense, start, end
        )
        if not rows:
            return None

        total = sum(a for _, a in rows)

        # Income sources + balance for the month.
        income_report, expense_total = await self._analytics.month_balance(user)
        lines: list[str] = []
        if income_report.rows:
            lines.append("Доходы за месяц по источникам:")
            for r in income_report.rows:
                lines.append(f"- {r.name}: {r.total:.0f} ₸")
            lines.append(f"Всего доходов: {income_report.total:.0f} ₸.")
        balance = income_report.total - expense_total
        lines.append(
            f"Баланс за месяц: {balance:.0f} ₸ "
            f"({'профицит' if balance >= 0 else 'дефицит'})."
        )

        lines += [f"Расходы за месяц: {total:.0f} ₸.", "Категории расходов:"]
        for name, amount in rows:
            share = amount / total * 100.0 if total else 0.0
            lines.append(f"- {name}: {amount:.0f} ₸ ({share:.0f}%)")

        rule = await self.fifty_thirty_twenty(user)
        if rule is not None:
            lines.append(
                f"Доход: {rule.income:.0f} ₸. "
                f"Нужное {rule.needs_pct:.0f}% (цель 50%), "
                f"хотелки {rule.wants_pct:.0f}% (цель 30%), "
                f"остаётся {rule.savings_pct:.0f}% (цель 20%)."
            )

        anomalies = await self._analytics.detect_anomalies(user)
        if anomalies:
            joined = ", ".join(
                f"{a['category']} +{(a['ratio'] - 1) * 100:.0f}%"  # type: ignore[operator]
                for a in anomalies[:3]
            )
            lines.append(f"Резкий рост vs обычного: {joined}.")

        subs = await self._analytics.detect_subscriptions(user)
        if subs:
            sub_total = sum(float(s["amount"]) for s in subs)  # type: ignore[arg-type]
            names = ", ".join(str(s["description"]) for s in subs[:5])
            lines.append(
                f"Похоже на подписки/регулярные платежи на ~{sub_total:.0f} ₸/мес "
                f"({names})."
            )

        # Deviations from the KZ average (shares of spending).
        bench = await self.benchmark(user)
        deviations = [
            f"{name}: {u:.0f}% vs средних {kz:.0f}%"
            for name, u, kz in bench
            if abs(u - kz) >= 7
        ][:3]
        if deviations:
            lines.append("Отклонения от среднего по РК: " + "; ".join(deviations) + ".")

        return "\n".join(lines)

    async def benchmark(self, user: User) -> list[tuple[str, float, float]]:
        """Compare the user's category shares with the KZ reference (%)."""
        shares = await self._analytics.month_shares(user)
        return benchmarks.compare_shares(shares)
