"""Small, strategy-neutral analytics for canonical OHLCV rows.

These helpers intentionally stop at reusable market-data transformations. They do
not generate buy/sell signals, portfolio recommendations, or order instructions.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from .calendar import TaiwanTradingCalendar
from .validation import OHLCVRow

PriceField = Literal["open", "high", "low", "close"]


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    """One dated value in a derived market-data series."""

    date: date
    value: Decimal


@dataclass(frozen=True, slots=True)
class OHLCVSummary:
    """Basic descriptive information for a normalized OHLCV series."""

    rows: int
    start: date | None
    end: date | None
    min_close: Decimal | None
    max_close: Decimal | None
    total_volume: int


def _price(row: OHLCVRow, field: PriceField) -> Decimal:
    return getattr(row, field)


def _validate_window(window: int) -> None:
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")


def simple_moving_average(
    rows: list[OHLCVRow],
    window: int,
    *,
    field: PriceField = "close",
) -> list[SeriesPoint]:
    """Return a full-window simple moving average for a price field.

    The first point is emitted only after ``window`` observations are available.
    Input order is preserved; callers should normalize/sort their data first when
    chronological output is required.
    """
    _validate_window(window)
    if len(rows) < window:
        return []

    values: deque[Decimal] = deque()
    running = Decimal(0)
    result: list[SeriesPoint] = []

    for row in rows:
        value = _price(row, field)
        values.append(value)
        running += value

        if len(values) > window:
            running -= values.popleft()

        if len(values) == window:
            result.append(SeriesPoint(row.date, running / Decimal(window)))

    return result


def exponential_moving_average(
    rows: list[OHLCVRow],
    window: int,
    *,
    field: PriceField = "close",
) -> list[SeriesPoint]:
    """Return an EMA seeded by the first full-window SMA.

    The smoothing factor is ``2 / (window + 1)``. As with the SMA helper, points
    begin only after a complete initial window is available.
    """
    _validate_window(window)
    if len(rows) < window:
        return []

    seed_rows = rows[:window]
    seed = sum((_price(row, field) for row in seed_rows), Decimal(0)) / Decimal(window)
    alpha = Decimal(2) / Decimal(window + 1)

    result = [SeriesPoint(seed_rows[-1].date, seed)]
    previous = seed

    for row in rows[window:]:
        current = (_price(row, field) - previous) * alpha + previous
        result.append(SeriesPoint(row.date, current))
        previous = current

    return result


def daily_returns(
    rows: list[OHLCVRow],
    *,
    field: PriceField = "close",
) -> list[SeriesPoint]:
    """Return one-period fractional returns, e.g. ``0.01`` for one percent."""
    if len(rows) < 2:
        return []

    result: list[SeriesPoint] = []
    previous = _price(rows[0], field)

    for row in rows[1:]:
        current = _price(row, field)
        if previous == 0:
            raise ValueError("cannot calculate return after a zero price")
        result.append(SeriesPoint(row.date, (current / previous) - Decimal(1)))
        previous = current

    return result


def summarize_ohlcv(rows: list[OHLCVRow]) -> OHLCVSummary:
    """Return basic descriptive statistics without changing row order."""
    if not rows:
        return OHLCVSummary(
            rows=0,
            start=None,
            end=None,
            min_close=None,
            max_close=None,
            total_volume=0,
        )

    dates = [row.date for row in rows]
    closes = [row.close for row in rows]
    return OHLCVSummary(
        rows=len(rows),
        start=min(dates),
        end=max(dates),
        min_close=min(closes),
        max_close=max(closes),
        total_volume=sum(row.volume for row in rows),
    )


def find_missing_trading_days(
    rows: list[OHLCVRow],
    calendar: TaiwanTradingCalendar,
) -> list[date]:
    """Find expected trading dates absent between the first and last observation.

    Callers should use an exchange-aware calendar when holiday accuracy matters.
    The function intentionally requires an explicit calendar instead of assuming
    that every weekday is an exchange trading day.
    """
    if len(rows) < 2:
        return []

    observed = {row.date for row in rows}
    start = min(observed)
    end = max(observed)
    return [day for day in calendar.trading_days(start, end) if day not in observed]
