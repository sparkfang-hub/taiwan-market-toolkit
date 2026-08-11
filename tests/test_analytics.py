from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.analytics import (
    daily_returns,
    exponential_moving_average,
    find_missing_trading_days,
    simple_moving_average,
    summarize_ohlcv,
)
from taiwan_market_toolkit.calendar import TaiwanTradingCalendar
from taiwan_market_toolkit.validation import OHLCVRow


def _row(day: int, close: str, *, volume: int = 100) -> OHLCVRow:
    price = Decimal(close)
    return OHLCVRow(
        date=date(2026, 8, day),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=volume,
    )


def test_simple_moving_average_uses_full_windows():
    rows = [_row(10, "10"), _row(11, "20"), _row(12, "30"), _row(13, "40")]

    points = simple_moving_average(rows, 3)

    assert [point.date for point in points] == [date(2026, 8, 12), date(2026, 8, 13)]
    assert [point.value for point in points] == [Decimal("20"), Decimal("30")]


def test_simple_moving_average_supports_other_price_fields():
    row1 = OHLCVRow(date(2026, 8, 10), Decimal("1"), Decimal("4"), Decimal("1"), Decimal("2"), 1)
    row2 = OHLCVRow(date(2026, 8, 11), Decimal("2"), Decimal("6"), Decimal("2"), Decimal("3"), 1)

    points = simple_moving_average([row1, row2], 2, field="high")

    assert points[0].value == Decimal("5")


def test_exponential_moving_average_is_seeded_with_sma():
    rows = [_row(10, "10"), _row(11, "20"), _row(12, "30"), _row(13, "40")]

    points = exponential_moving_average(rows, 3)

    assert points[0].value == Decimal("20")
    assert points[1].value == Decimal("30")


def test_daily_returns_are_fractional():
    rows = [_row(10, "100"), _row(11, "110"), _row(12, "99")]

    points = daily_returns(rows)

    assert points[0].value == Decimal("0.1")
    assert points[1].value == Decimal("-0.1")


def test_summary_handles_non_empty_and_empty_series():
    rows = [_row(10, "100", volume=10), _row(11, "90", volume=20)]

    summary = summarize_ohlcv(rows)
    empty = summarize_ohlcv([])

    assert summary.rows == 2
    assert summary.start == date(2026, 8, 10)
    assert summary.end == date(2026, 8, 11)
    assert summary.min_close == Decimal("90")
    assert summary.max_close == Decimal("100")
    assert summary.total_volume == 30
    assert empty.rows == 0
    assert empty.start is None


def test_find_missing_trading_days_uses_explicit_calendar():
    rows = [_row(10, "100"), _row(13, "103")]
    calendar = TaiwanTradingCalendar.from_overrides(closures=[date(2026, 8, 12)])

    missing = find_missing_trading_days(rows, calendar)

    assert missing == [date(2026, 8, 11)]


@pytest.mark.parametrize("window", [0, -1, True])
def test_invalid_windows_are_rejected(window):
    with pytest.raises(ValueError, match="positive integer"):
        simple_moving_average([_row(10, "1")], window)
