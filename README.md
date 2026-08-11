# Taiwan Market Toolkit

Open-source Python utilities for working with Taiwan stock-market data.

The project focuses on small, composable building blocks that can be reused in research pipelines, trading tools, data-quality checks, and AI-agent workflows without exposing proprietary strategies.

## Current capabilities

- Normalize Taiwan tickers such as `2330`, `2330.TW`, and `6488.TWO`.
- Represent TWSE and TPEx market identifiers consistently.
- Query a lightweight Taiwan trading calendar with custom closure dates.
- Validate OHLCV rows for malformed prices, negative volume, duplicates, and ordering issues.
- Use a small CLI for symbol and calendar operations.
- Run automated tests on Python 3.10, 3.11, and 3.12 through GitHub Actions.

## Installation

The project is currently in early development. Install directly from a clone:

```bash
git clone https://github.com/sparkfang-hub/taiwan-market-toolkit.git
cd taiwan-market-toolkit
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Quick start

### Normalize symbols

```python
from taiwan_market_toolkit import normalize_symbol

symbol = normalize_symbol("2330.TW")
print(symbol.code)    # 2330
print(symbol.market)  # Market.TWSE
print(symbol.yahoo)   # 2330.TW
```

A market hint can be supplied for a bare ticker:

```python
normalize_symbol("6488", "TPEX").yahoo
# '6488.TWO'
```

### Trading calendar

```python
from datetime import date
from taiwan_market_toolkit import TaiwanTradingCalendar

calendar = TaiwanTradingCalendar()
calendar.is_trading_day(date(2026, 8, 10))
calendar.next_trading_day(date(2026, 8, 7))
```

Important: the v0.1 calendar does not bundle an exchange holiday database. It treats weekends as closed and accepts explicit closure dates. This avoids silently shipping stale holiday assumptions while a verified calendar data source is being designed.

### Validate OHLCV data

```python
from datetime import date
from decimal import Decimal
from taiwan_market_toolkit import OHLCVRow, validate_ohlcv

rows = [
    OHLCVRow(
        date=date(2026, 8, 10),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("95"),
        close=Decimal("105"),
        volume=1000,
    )
]

issues = validate_ohlcv(rows)
```

### CLI

```bash
tw-market symbol 2330.TW
tw-market symbol 6488 --market TPEX
tw-market calendar 2026-08-07 --next
```

## Project scope

Taiwan Market Toolkit is infrastructure, not a trading strategy. The project aims to make Taiwan-market data easier to normalize, validate, query, and expose to other software.

Planned areas include:

- verified TWSE/TPEx trading-calendar providers;
- tabular OHLCV normalization;
- market metadata and security-master helpers;
- data-source adapters with explicit licensing and provenance;
- richer validation and anomaly reporting;
- optional MCP tools for AI-agent workflows.

The project does not provide investment advice, trading signals, portfolio recommendations, or guaranteed market-data accuracy.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` before opening a pull request. In particular, do not submit proprietary datasets, API credentials, private trading strategies, or data that cannot legally be redistributed.

## License

MIT License. See `LICENSE`.
