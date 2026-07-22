"""Clear unfinished text-entry flows when a persistent menu button is used."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import MENU_BUTTONS


class ClearMenuStateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if event.text in MENU_BUTTONS and isinstance(state, FSMContext):
            await state.clear()
        return await handler(event, data)
