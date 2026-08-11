"""OHLCV validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True, slots=True)
class OHLCVRow:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    row: int
    code: str
    message: str


def validate_ohlcv(rows: Iterable[OHLCVRow]) -> list[ValidationIssue]:
    """Validate ordering and basic OHLCV invariants.

    This intentionally checks data quality only; it does not attempt to decide
    whether an unusual price move is economically plausible.
    """
    issues: list[ValidationIssue] = []
    previous_date: date | None = None
    seen_dates: set[date] = set()

    for index, item in enumerate(rows, start=1):
        prices = (item.open, item.high, item.low, item.close)
        if any(price <= 0 for price in prices):
            issues.append(ValidationIssue(index, "non_positive_price", "Prices must be positive."))

        if item.high < max(item.open, item.close, item.low):
            issues.append(ValidationIssue(index, "invalid_high", "High must be the maximum OHLC price."))
        if item.low > min(item.open, item.close, item.high):
            issues.append(ValidationIssue(index, "invalid_low", "Low must be the minimum OHLC price."))
        if item.volume < 0:
            issues.append(ValidationIssue(index, "negative_volume", "Volume cannot be negative."))

        if item.date in seen_dates:
            issues.append(ValidationIssue(index, "duplicate_date", f"Duplicate date: {item.date.isoformat()}"))
        seen_dates.add(item.date)

        if previous_date is not None and item.date < previous_date:
            issues.append(ValidationIssue(index, "out_of_order", "Rows must be sorted by ascending date."))
        previous_date = item.date

    return issues
