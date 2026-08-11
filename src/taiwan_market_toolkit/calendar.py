"""Lightweight Taiwan trading-calendar helpers.

The core calendar deliberately avoids shipping a stale holiday table. Weekends are
closed by default, while exchange-specific closure dates can be supplied by users
or future data providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from collections.abc import Iterable


@dataclass(slots=True)
class TaiwanTradingCalendar:
    """Determine trading days using weekends plus explicit closure dates."""

    closures: set[date] = field(default_factory=set)

    @classmethod
    def from_closures(cls, closures: Iterable[date]) -> "TaiwanTradingCalendar":
        return cls(set(closures))

    def is_trading_day(self, day: date) -> bool:
        """Return ``True`` when *day* is a weekday and not explicitly closed."""
        return day.weekday() < 5 and day not in self.closures

    def next_trading_day(self, day: date, *, include_current: bool = False) -> date:
        """Return the next trading day after *day* (or including it when requested)."""
        current = day if include_current else day + timedelta(days=1)
        while not self.is_trading_day(current):
            current += timedelta(days=1)
        return current

    def previous_trading_day(self, day: date, *, include_current: bool = False) -> date:
        """Return the previous trading day before *day*."""
        current = day if include_current else day - timedelta(days=1)
        while not self.is_trading_day(current):
            current -= timedelta(days=1)
        return current

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return trading days in the inclusive date range."""
        if end < start:
            raise ValueError("end must be on or after start")
        days: list[date] = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days
