# Taiwan Market Toolkit

Open-source Python utilities for working with Taiwan stock-market data.

The project focuses on small, composable building blocks that can be reused in research pipelines, trading tools, data-quality checks, and AI-agent workflows without exposing proprietary strategies.

## Current capabilities

- Normalize Taiwan tickers such as `2330`, `2330.TW`, and `6488.TWO`.
- Represent TWSE and TPEx market identifiers consistently.
- Query a Taiwan trading calendar with explicit closure/opening overrides.
- Fetch and parse the official TWSE market holiday schedule from TWSE OpenAPI.
- Normalize records, CSV files, and pandas-like DataFrames into one OHLCV schema.
- Validate OHLCV rows for malformed prices, negative volume, duplicates, and ordering issues.
- Use a CLI for symbol, calendar, and CSV validation operations.
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

Explicit openings are supported as well as closures, which matters if the exchange announces a supplemental weekend trading day:

```python
calendar = TaiwanTradingCalendar.from_overrides(
    closures=[date(2026, 1, 1)],
    openings=[date(2026, 1, 3)],
)
```

### Official TWSE holiday schedule

TWSE publishes an official OpenAPI endpoint for the currently published market open/closure schedule. The toolkit can fetch that schedule and turn it into a ready-to-query calendar:

```python
from taiwan_market_toolkit import fetch_twse_calendar

calendar = fetch_twse_calendar()
```

Network access is kept separate from parsing so applications can cache the official response or supply fixtures in tests:

```python
from taiwan_market_toolkit import (
    calendar_from_twse_records,
    parse_twse_holiday_payload,
)

records = parse_twse_holiday_payload(cached_json)
calendar = calendar_from_twse_records(records)
```

Source: Taiwan Stock Exchange OpenAPI, `holidaySchedule/holidaySchedule`.

The provider deliberately does not maintain a copied hard-coded holiday table. The official response remains the source of truth, while applications that require reproducible historical runs should cache the exact payload they used.

### Normalize OHLCV data

Common column aliases are detected automatically:

```python
from taiwan_market_toolkit import normalize_ohlcv_records

rows = normalize_ohlcv_records(
    [
        {
            "Trading Date": "2026/08/11",
            "Open Price": "101.5",
            "High Price": "110",
            "Low Price": "100",
            "Close": "108.5",
            "Vol": "1,200",
        }
    ]
)
```

For unusual source schemas, pass an explicit mapping from canonical names to source columns:

```python
rows = normalize_ohlcv_records(
    records,
    column_map={
        "date": "交易日期",
        "open": "開盤價",
        "high": "最高價",
        "low": "最低價",
        "close": "收盤價",
        "volume": "成交股數",
    },
)
```

CSV text/files and pandas-like DataFrames are also supported through `parse_ohlcv_csv`, `read_ohlcv_csv`, and `dataframe_to_ohlcv`. Pandas is not a required dependency.

### Validate OHLCV data

```python
from taiwan_market_toolkit import normalize_and_validate_ohlcv_records

result = normalize_and_validate_ohlcv_records(records)
for issue in result.issues:
    print(issue.code, issue.message)
```

Validation checks OHLC price invariants, negative volume, duplicate dates, and chronological ordering. Normalization and validation are intentionally separate so callers can choose whether to sort input before checking it.

### CLI

```bash
tw-market symbol 2330.TW
tw-market symbol 6488 --market TPEX
tw-market calendar 2026-08-07 --next
tw-market validate prices.csv
tw-market validate prices.csv --no-sort
```

The `validate` command prints JSON with row count, validity, and individual issues.

## Project scope

Taiwan Market Toolkit is infrastructure, not a trading strategy. The project aims to make Taiwan-market data easier to normalize, validate, query, and expose to other software.

Planned areas include:

- richer TWSE/TPEx trading-calendar providers and caching;
- market metadata and security-master helpers;
- data-source adapters with explicit licensing and provenance;
- richer validation and anomaly reporting;
- optional MCP tools for AI-agent workflows.

The project does not provide investment advice, trading signals, portfolio recommendations, or guaranteed market-data accuracy.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` before opening a pull request. In particular, do not submit proprietary datasets, API credentials, private trading strategies, or data that cannot legally be redistributed.

## License

MIT License. See `LICENSE`.
