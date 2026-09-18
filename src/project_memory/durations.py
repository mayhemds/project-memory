"""Parsing of human duration strings such as ``24h``, ``7d``, and ``30m``."""

from __future__ import annotations

import re
from datetime import timedelta

from .exceptions import MemError

_UNIT_MINUTES: dict[str, int] = {"m": 1, "h": 60, "d": 1440}
_DURATION_PATTERN = re.compile(r"^(?P<amount>\d+)(?P<unit>[mhd])$")


def parse_duration(text: str) -> timedelta:
    """Parse a duration string into a :class:`~datetime.timedelta`.

    Args:
        text: A positive integer followed by a single unit character: ``m``
            for minutes, ``h`` for hours, or ``d`` for days. For example,
            ``7d`` means seven days.

    Returns:
        The equivalent timedelta.

    Raises:
        MemError: If the string does not match the expected format, or the
            amount is zero.
    """
    match = _DURATION_PATTERN.match(text.strip())
    if match is None:
        raise MemError(
            f"Invalid duration {text!r}. Use a number followed by m, h, or d, e.g. '7d'."
        )
    amount = int(match.group("amount"))
    if amount <= 0:
        raise MemError(f"Duration must be a positive number, got {text!r}.")
    return timedelta(minutes=amount * _UNIT_MINUTES[match.group("unit")])
