"""Parse free-text money messages into structured data via Gemini.

Uses Gemini *controlled generation* (``response_schema`` +
``response_mime_type="application/json"``). This is the Gemini equivalent of
tool/function calling for a guaranteed-valid JSON payload: the model is
constrained to emit exactly the :class:`ParsedTransaction` shape, so we never
have to defensively parse malformed output.

The actual API call (with retries + fallback model) lives in
:mod:`app.services.gemini`.
"""

from __future__ import annotations

import structlog

from app.services import gemini
from app.services.schemas import ParsedTransaction

log = structlog.get_logger(__name__)

_SYSTEM_INSTRUCTION = """
Ты — парсер личных финансов. На вход приходит сообщение на русском или
английском об одной трате или доходе (например: "кофе 800", "такси 1500",
"зарплата 400000", "мне поступило 100 тенге", "донат в игру 300").

Извлеки:
- amount: положительное число (только сумма, без валюты; "125к" = 125000).
- category: одна наиболее подходящая категория. Предпочитай стандартные:
  Еда, Транспорт, Жильё, Развлечения, Здоровье, Другое. Если явно не подходит —
  выбери "Другое".
- type: "income" для доходов (зарплата, перевод, поступление, кэшбэк),
  иначе "expense".
- description: краткое описание из сообщения.

Если в сообщении несколько сумм — возьми основную сумму операции.
Если суммы нет вообще — верни amount = 0.
""".strip()


class ExpenseParseError(RuntimeError):
    """Raised when the model returned no usable transaction."""


class ParserService:
    """Turns free text into a :class:`ParsedTransaction` via Gemini."""

    async def parse(self, text: str) -> ParsedTransaction:
        """Parse ``text`` into a :class:`ParsedTransaction`.

        Raises :class:`ExpenseParseError` if the model cannot extract a
        positive amount. Transient Gemini errors (503/429) are retried
        internally; a persistent failure propagates as the original API error.
        """
        parsed = await gemini.generate_json(
            contents=text,
            schema=ParsedTransaction,
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=0.0,
        )
        if parsed is None:
            raise ExpenseParseError("model returned no structured output")
        if parsed.amount <= 0:
            raise ExpenseParseError(f"no amount in message: {text!r}")

        log.info(
            "expense_parsed",
            amount=parsed.amount,
            category=parsed.category,
            type=parsed.type.value,
        )
        return parsed
