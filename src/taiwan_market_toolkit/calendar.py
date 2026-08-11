"""Lightweight Taiwan trading-calendar helpers.

Weekends are closed by default. Explicit closures can override weekdays, while
explicit openings can represent exchange-announced supplemental trading days.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(slots=True)
class TaiwanTradingCalendar:
    """Determine trading days from weekends plus explicit exchange overrides."""

    closures: set[date] = field(default_factory=set)
    openings: set[date] = field(default_factory=set)

    @classmethod
    def from_closures(cls, closures: Iterable[date]) -> TaiwanTradingCalendar:
        """Build a calendar from explicit closure dates."""
        return cls(closures=set(closures))

    @classmethod
    def from_overrides(
        cls,
        *,
        closures: Iterable[date] = (),
        openings: Iterable[date] = (),
    ) -> TaiwanTradingCalendar:
        """Build a calendar from explicit closure and opening dates."""
        closure_set = set(closures)
        opening_set = set(openings)
        overlap = closure_set & opening_set
        if overlap:
            joined = ", ".join(sorted(day.isoformat() for day in overlap))
            raise ValueError(f"Dates cannot be both closed and open: {joined}")
        return cls(closures=closure_set, openings=opening_set)

    def is_trading_day(self, day: date) -> bool:
        """Return whether *day* is open for trading."""
        if day in self.closures:
            return False
        if day in self.openings:
            return True
        return day.weekday() < 5

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
