from datetime import date

import pytest

from taiwan_market_toolkit import TaiwanTradingCalendar


def test_weekend_is_closed():
    calendar = TaiwanTradingCalendar()
    assert not calendar.is_trading_day(date(2026, 8, 9))


def test_weekday_is_open_without_explicit_closure():
    calendar = TaiwanTradingCalendar()
    assert calendar.is_trading_day(date(2026, 8, 10))


def test_explicit_closure_is_closed():
    closed = date(2026, 8, 10)
    calendar = TaiwanTradingCalendar.from_closures([closed])
    assert not calendar.is_trading_day(closed)


def test_explicit_opening_can_open_weekend():
    opened = date(2026, 8, 9)
    calendar = TaiwanTradingCalendar.from_overrides(openings=[opened])
    assert calendar.is_trading_day(opened)


def test_conflicting_override_rejected():
    day = date(2026, 8, 10)
    with pytest.raises(ValueError, match="both closed and open"):
        TaiwanTradingCalendar.from_overrides(closures=[day], openings=[day])


def test_next_trading_day_skips_weekend():
    calendar = TaiwanTradingCalendar()
    assert calendar.next_trading_day(date(2026, 8, 7)) == date(2026, 8, 10)
