# Taiwan Market Toolkit

Open-source Python utilities for working with Taiwan stock-market data.

The project focuses on small, composable building blocks that can be reused in research pipelines, trading tools, data-quality checks, and AI-agent workflows without exposing proprietary strategies.

## Why this project exists

Taiwan-market data often carries details that generic market-data libraries do not handle well out of the box: TWSE/TPEx ticker suffixes, ROC-calendar dates, Traditional Chinese column names, exchange-specific holiday schedules, and source-specific CSV schemas. Taiwan Market Toolkit aims to normalize those edges behind a small, testable API.

The project is infrastructure, not a trading strategy. It deliberately excludes private signals, brokerage credentials, portfolio recommendations, and order execution.

## Current capabilities

- Normalize Taiwan tickers such as `2330`, `2330.TW`, and `6488.TWO`.
- Represent TWSE and TPEx market identifiers consistently.
- Fetch a small common closing-quote snapshot from the official TWSE or TPEx OpenAPI without brokerage credentials.
- Query a Taiwan trading calendar with explicit closure/opening overrides.
- Fetch and parse the official TWSE market holiday schedule from TWSE OpenAPI.
- Normalize records, CSV files, and pandas-like DataFrames into one OHLCV schema.
- Recognize common Traditional Chinese OHLCV headers such as `交易日期`, `開盤價`, `最高價`, `最低價`, `收盤價`, and `成交股數`.
- Parse common ROC-calendar dates such as `115/08/11` and `1150811`.
- Validate OHLCV rows for malformed prices, negative volume, duplicates, and ordering issues.
- Calculate strategy-neutral SMA, EMA, daily returns, descriptive summaries, and missing trading dates.
- Use a CLI for symbol, quote, calendar, validation, and OHLCV analysis operations.
- Expose read-only market utilities and descriptive analytics to AI hosts through an optional MCP server.
- Build and test on Python 3.10, 3.11, and 3.12 through GitHub Actions.
- Build and validate wheel/source distributions on every pull request.
- Run a separate scheduled smoke check against official exchange sources so normal unit tests can stay deterministic.

## Installation

The project is in alpha development. Until the first PyPI release, install from a clone:

```bash
git clone https://github.com/sparkfang-hub/taiwan-market-toolkit.git
cd taiwan-market-toolkit
python -m pip install -e .
```

After the first PyPI release, the intended installation command is:

```bash
python -m pip install taiwan-market-toolkit
```

For MCP support:

```bash
python -m pip install -e '.[mcp]'
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

### Official closing quotes

Fetch one latest official closing snapshot by using an exchange suffix or an explicit market hint:

```python
from taiwan_market_toolkit import fetch_closing_quote

quote = fetch_closing_quote("2330.TW")
print(quote.date)
print(quote.code)
print(quote.name)
print(quote.market)
print(quote.close)
```

The common `ClosingQuote` model intentionally contains only fields with clear shared meaning across the two exchanges: market, trading date, security code, name, and closing price. Exchange-specific details remain in the original official payload instead of being guessed into a common schema.

For batch workflows, the raw adapters are also public:

```python
from taiwan_market_toolkit import fetch_tpex_closing_quotes, fetch_twse_closing_quotes

twse_rows = fetch_twse_closing_quotes()
tpex_rows = fetch_tpex_closing_quotes()
```

### Trading calendar

```python
from datetime import date
from taiwan_market_toolkit import TaiwanTradingCalendar

calendar = TaiwanTradingCalendar()
calendar.is_trading_day(date(2026, 8, 10))
calendar.next_trading_day(date(2026, 8, 7))
```

Explicit openings are supported as well as closures, which matters if an exchange announces a supplemental trading day:

```python
calendar = TaiwanTradingCalendar.from_overrides(
    closures=[date(2026, 1, 1)],
    openings=[date(2026, 1, 3)],
)
```

### Official TWSE holiday schedule

TWSE publishes an official OpenAPI endpoint for its published market open/closure schedule. The toolkit can fetch that schedule and turn it into a ready-to-query calendar:

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

### Normalize English OHLCV data

Common English column aliases are detected automatically:

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

### Normalize Traditional Chinese OHLCV data

Common Taiwan-style headers and ROC-calendar dates can be ingested without a custom mapping:

```python
from taiwan_market_toolkit import normalize_ohlcv_records

rows = normalize_ohlcv_records(
    [
        {
            "交易日期": "115/08/11",
            "開盤價": "101.5",
            "最高價": "110",
            "最低價": "100",
            "收盤價": "108.5",
            "成交股數": "1,200",
        }
    ]
)

print(rows[0].date)  # 2026-08-11
```

For unusual source schemas, pass an explicit mapping from canonical names to source columns:

```python
rows = normalize_ohlcv_records(
    records,
    column_map={
        "date": "日期欄位",
        "open": "開盤欄位",
        "high": "最高欄位",
        "low": "最低欄位",
        "close": "收盤欄位",
        "volume": "成交量欄位",
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

### Descriptive analytics

Moving averages and returns operate on the normalized OHLCV representation and do not generate trading signals:

```python
from taiwan_market_toolkit import (
    daily_returns,
    exponential_moving_average,
    simple_moving_average,
    summarize_ohlcv,
)

summary = summarize_ohlcv(rows)
sma20 = simple_moving_average(rows, 20)
ema20 = exponential_moving_average(rows, 20)
returns = daily_returns(rows)
```

To audit gaps, provide an explicit exchange-aware calendar rather than assuming every weekday is a trading day:

```python
from taiwan_market_toolkit import find_missing_trading_days

missing = find_missing_trading_days(rows, calendar)
```

### CLI

```bash
tw-market symbol 2330.TW
tw-market quote 2330.TW
tw-market quote 6488 --market TPEX
tw-market calendar 2026-08-07 --next
tw-market validate examples/sample_ohlcv_zh.csv
tw-market validate prices.csv --no-sort
tw-market analyze prices.csv --sma 5 --sma 20 --ema 20
```

The `quote` command performs a read-only request to the relevant official exchange OpenAPI. The `validate` command reports data-quality issues. The `analyze` command reports the date range, close range, total volume, latest fractional return, and any caller-selected SMA/EMA windows as JSON.

## MCP server

The optional MCP server uses the official MCP Python SDK v2 and keeps AI-facing tools separate from private trading logic.

Install the optional dependency and start a local stdio server:

```bash
python -m pip install -e '.[mcp]'
tw-market-mcp
```

The server currently exposes:

- `normalize_taiwan_symbol` — normalize TWSE/TPEx-style tickers;
- `get_official_closing_quote` — fetch one read-only official TWSE/TPEx closing snapshot;
- `check_trading_day` — apply weekend rules plus caller-supplied closures/openings;
- `check_twse_trading_day` — query the official TWSE OpenAPI schedule;
- `validate_ohlcv_csv_text` — normalize and validate CSV-formatted OHLCV data;
- `analyze_ohlcv_csv_text` — summarize OHLCV data and calculate caller-selected SMA/EMA windows;
- `taiwan-market://about` — describe the project scope and safety boundary.

The MCP surface requires no brokerage credentials and provides no order execution. Exchange-backed tools perform read-only requests to public official sources.

For development, the official MCP Inspector can load the server module:

```bash
mcp dev src/taiwan_market_toolkit/mcp_server.py --with-editable .
```

## Runnable examples

The `examples/` directory contains copy-pasteable examples for:

- validating a Traditional Chinese CSV with ROC-calendar dates;
- querying the official TWSE calendar provider;
- calling toolkit functions through an in-memory MCP client.

See `examples/README.md` for commands.

## Packaging and releases

Pull requests build both a wheel and source distribution and validate package metadata. The repository also contains a PyPI Trusted Publishing workflow that runs when a GitHub release is published.

Before the first release, the maintainer must register the GitHub workflow as a PyPI Trusted Publisher and configure the protected `pypi` GitHub environment. See `docs/releasing.md` for the release checklist.

## Data sources and provenance

Market integrations use authoritative public sources where possible and keep fetching separate from parsing. Source adapters document provenance, update behavior, licensing/terms considerations, and failure behavior.

Current implemented official sources include:

- TWSE `STOCK_DAY_ALL` for the listed-market closing snapshot;
- TPEx `tpex_mainboard_daily_close_quotes` for the OTC main-board closing snapshot;
- TWSE `holidaySchedule/holidaySchedule` for the listed-market calendar.

Normal CI uses fixtures rather than live network calls. A separate scheduled/manual source smoke check probes implemented official endpoints so upstream schema or availability changes are visible without making every pull request depend on exchange uptime.

See `docs/data-sources.md` for the detailed provenance and reliability policy.

## Project scope and roadmap

Planned areas include:

- verified TPEx holiday-calendar support;
- market metadata and security-master helpers;
- additional official TWSE/TPEx data-source adapters;
- richer validation and anomaly reporting;
- additional read-only MCP tools around stable toolkit capabilities;
- packaging and release hardening based on real user feedback.

The project does not provide investment advice, trading signals, portfolio recommendations, or guaranteed market-data accuracy.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` before opening a pull request. In particular, do not submit proprietary datasets, API credentials, private trading strategies, or data that cannot legally be redistributed.

Good first issues are intentionally kept small enough for new contributors to understand the codebase and submit focused pull requests.

## License

MIT License. See `LICENSE`.
