"""Check a date against the official TWSE holiday schedule."""

from datetime import date

from taiwan_market_toolkit import fetch_twse_calendar


calendar = fetch_twse_calendar()
target = date.today()

print(f"date={target.isoformat()}")
print(f"trading_day={calendar.is_trading_day(target)}")
print(f"next_trading_day={calendar.next_trading_day(target, include_current=True)}")
