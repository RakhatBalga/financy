"""Parse free-text money messages into structured data via Gemini.

Uses Gemini *controlled generation* (``response_schema`` +
``response_mime_type="application/json"``). This is the Gemini equivalent of
tool/function calling for a guaranteed-valid JSON payload: the model is
constrained to emit exactly the :class:`ParsedTransaction` shape, so we never
have to defensively parse malformed output.
"""

from __future__ import annotations

import json

import structlog
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.schemas import ParsedTransaction

log = structlog.get_logger(__name__)

_SYSTEM_INSTRUCTION = """
Ты — парсер личных финансов. На вход приходит короткое сообщение на русском
или английском об одной трате или доходе (например: "кофе 800",
"такси 1500", "зарплата 400000", "продукты магнит 12000").

Извлеки:
- amount: положительное число (только сумма, без валюты).
- category: одна наиболее подходящая категория. Предпочитай стандартные:
  Еда, Транспорт, Жильё, Развлечения, Здоровье, Другое. Если явно не подходит —
  выбери "Другое".
- type: "income" для доходов (зарплата, перевод, кэшбэк), иначе "expense".
- description: краткое описание товара/услуги из сообщения.

Если суммы нет — верни amount = 0.
""".strip()


class ExpenseParseError(RuntimeError):
    """Raised when the model returned no usable transaction."""


class ParserService:
    """Wraps the Gemini client for expense parsing."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._model = model or settings.gemini_model
        self._client = genai.Client(api_key=api_key or settings.gemini_api_key)

    async def parse(self, text: str) -> ParsedTransaction:
        """Parse ``text`` into a :class:`ParsedTransaction`.

        Raises :class:`ExpenseParseError` if the model cannot extract a
        positive amount.
        """
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ParsedTransaction,
                temperature=0.0,
            ),
        )

        parsed = self._extract(response)
        if parsed.amount <= 0:
            raise ExpenseParseError(f"no amount in message: {text!r}")

        log.info(
            "expense_parsed",
            amount=parsed.amount,
            category=parsed.category,
            type=parsed.type.value,
        )
        return parsed

    @staticmethod
    def _extract(response: types.GenerateContentResponse) -> ParsedTransaction:
        """Pull the validated object out of the Gemini response.

        ``response.parsed`` is populated by the SDK when a ``response_schema``
        is used; fall back to manual JSON parsing just in case.
        """
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, ParsedTransaction):
            return parsed
        try:
            return ParsedTransaction.model_validate(json.loads(response.text))
        except (ValueError, TypeError) as exc:  # noqa: BLE001 - narrow enough
            raise ExpenseParseError("model returned invalid JSON") from exc
