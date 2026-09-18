"""Tests for duration parsing."""

from __future__ import annotations

from datetime import timedelta

import pytest

from project_memory.durations import parse_duration
from project_memory.exceptions import MemError


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("30m", timedelta(minutes=30)),
        ("1h", timedelta(hours=1)),
        ("24h", timedelta(hours=24)),
        ("7d", timedelta(days=7)),
        ("1m", timedelta(minutes=1)),
        ("365d", timedelta(days=365)),
    ],
)
def test_parse_duration_returns_expected_timedelta(text: str, expected: timedelta) -> None:
    assert parse_duration(text) == expected


def test_parse_duration_strips_surrounding_whitespace() -> None:
    assert parse_duration("  7d  ") == timedelta(days=7)


@pytest.mark.parametrize(
    "text",
    ["", "d", "7", "7w", "7D", "-7d", "1.5h", "seven days", "7dd", "0d", "0h"],
)
def test_parse_duration_rejects_invalid_input(text: str) -> None:
    with pytest.raises(MemError):
        parse_duration(text)


def test_parse_duration_rejects_zero_with_positive_number_message() -> None:
    with pytest.raises(MemError, match="positive number"):
        parse_duration("0m")
