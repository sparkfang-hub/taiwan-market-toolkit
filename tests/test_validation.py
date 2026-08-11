from datetime import date
from decimal import Decimal

from taiwan_market_toolkit import OHLCVRow, validate_ohlcv


def row(day: int, open_: str, high: str, low: str, close: str, volume: int) -> OHLCVRow:
    return OHLCVRow(
        date=date(2026, 8, day),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=volume,
    )


def test_valid_ohlcv_has_no_issues():
    issues = validate_ohlcv([row(10, "100", "110", "95", "105", 1000)])
    assert issues == []


def test_detects_invalid_high_and_negative_volume():
    issues = validate_ohlcv([row(10, "100", "99", "95", "105", -1)])
    codes = {issue.code for issue in issues}
    assert "invalid_high" in codes
    assert "negative_volume" in codes


def test_detects_duplicate_and_out_of_order_dates():
    rows = [
        row(11, "100", "110", "95", "105", 1000),
        row(11, "101", "111", "96", "106", 1000),
        row(10, "102", "112", "97", "107", 1000),
    ]
    codes = [issue.code for issue in validate_ohlcv(rows)]
    assert "duplicate_date" in codes
    assert "out_of_order" in codes
