"""Fetch one month of official TWSE history and calculate a simple moving average."""

from datetime import date

from taiwan_market_toolkit import fetch_price_history, history_to_ohlcv, simple_moving_average


prices = fetch_price_history(
    "2330.TW",
    start=date(2026, 7, 1),
    end=date(2026, 7, 31),
)
rows = history_to_ohlcv(prices)
sma5 = simple_moving_average(rows, 5)

print("observations:", len(prices))
if prices:
    print("range:", prices[0].date, "to", prices[-1].date)
if sma5:
    print("latest SMA5:", sma5[-1].date, sma5[-1].value)
