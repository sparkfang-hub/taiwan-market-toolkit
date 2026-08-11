from datetime import date

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


def test_next_trading_day_skips_weekend():
    calendar = TaiwanTradingCalendar()
    assert calendar.next_trading_day(date(2026, 8, 7)) == date(2026, 8, 10)
