"""Tests for human-friendly asset input formats."""

from app.bot.handlers.assets import _goal_input


def test_simple_goal_input_defaults_to_zero_kzt() -> None:
    assert _goal_input("квартира 30000000") == (
        "квартира",
        30_000_000,
        0,
        "KZT",
    )


def test_simple_goal_input_accepts_spaced_amount() -> None:
    assert _goal_input("новая квартира 30 000 000 KZT") == (
        "новая квартира",
        30_000_000,
        0,
        "KZT",
    )


def test_detailed_goal_input_keeps_current_amount() -> None:
    assert _goal_input("MacBook | 1500000 | 300000 KZT") == (
        "MacBook",
        1_500_000,
        300_000,
        "KZT",
    )
