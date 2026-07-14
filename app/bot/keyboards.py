"""Inline keyboards and their callback-data schema."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Category

# Callback data format: "confirm:<transaction_id>" / "recat:<transaction_id>"
# and for the category picker: "setcat:<transaction_id>:<category_id>".
CONFIRM_PREFIX = "confirm"
RECAT_PREFIX = "recat"
SETCAT_PREFIX = "setcat"


def confirm_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    """Confirm / change-category keyboard shown after a parsed transaction."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"{CONFIRM_PREFIX}:{transaction_id}",
        ),
        InlineKeyboardButton(
            text="✏️ Изменить категорию",
            callback_data=f"{RECAT_PREFIX}:{transaction_id}",
        ),
    )
    return builder.as_markup()


def category_picker_keyboard(
    transaction_id: int, categories: list[Category]
) -> InlineKeyboardMarkup:
    """Grid of the user's categories for reassigning a transaction."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"{SETCAT_PREFIX}:{transaction_id}:{category.id}",
        )
    builder.adjust(2)
    return builder.as_markup()
