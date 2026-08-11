# Taiwan Market Toolkit

Open-source Python utilities for working with Taiwan stock-market data from TWSE and TPEx.

Taiwan-market datasets have details that generic market libraries often leave to each application: `.TW`/`.TWO` symbols, ROC-calendar dates, Traditional Chinese CSV headers, exchange-specific company schemas, official closing snapshots, valuation fields, and holiday schedules. Taiwan Market Toolkit puts those edges behind small, testable APIs that can be reused by research pipelines, data-quality jobs, command-line tools, and AI agents.

This project is infrastructure, not a trading strategy. It deliberately excludes private signals, brokerage credentials, portfolio recommendations, and order execution.

## Current capabilities

- Normalize TWSE/TPEx tickers and market aliases.
- Fetch and search a unified company directory from official TWSE and TPEx basic-data sources.
- Fetch official closing snapshots for listed and TPEx main-board securities.
- Fetch common official valuation metrics: P/E ratio, dividend yield, and price-to-book ratio.
- Query a Taiwan trading calendar with explicit closure/opening overrides and the official TWSE holiday schedule.
- Normalize OHLCV records, CSV files, and pandas-like DataFrames.
- Recognize common Traditional Chinese headers such as `交易日期`, `開盤價`, `最高價`, `最低價`, `收盤價`, and `成交股數`.
- Parse Gregorian and common ROC-calendar dates such as `115/08/11` and `1150811`.
- Validate OHLCV price invariants, volume, duplicates, and ordering.
- Calculate strategy-neutral SMA, EMA, one-period returns, summaries, and missing trading dates.
- Preserve exact official closing-snapshot JSON locally with SHA-256 integrity metadata.
- Expose read-only market utilities through an optional MCP server.
- Test on Python 3.10, 3.11, and 3.12 and validate wheel/source distributions in CI.
- Run a separate scheduled smoke check against official exchange sources while keeping unit tests deterministic.

## Installation

The project is still in alpha and has not been rushed into a public package release. Install from a clone for now:

```bash
git clone https://github.com/sparkfang-hub/taiwan-market-toolkit.git
cd taiwan-market-toolkit
python -m pip install -e .
```

For MCP support:

```bash
python -m pip install -e '.[mcp]'
```

For development:

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Company directory

```python
from taiwan_market_toolkit import (
    fetch_company_directory,
    find_company,
    search_company_directory,
)

profile = find_company("2330.TW")
print(profile.short_name)
print(profile.industry)
print(profile.listing_date)

profiles = fetch_company_directory()
for item in search_company_directory(profiles, "台積"):
    print(item.code, item.short_name, item.market)
```

Bare tickers require an explicit market when the exchange cannot be inferred:

```python
find_company("6488", "TPEX")
```

The common `SecurityProfile` model keeps only identity fields that have clear cross-exchange meaning. See `docs/company-directory.md` for the source mapping and reliability boundary.

## Official closing quotes

```python
from taiwan_market_toolkit import fetch_closing_quote

quote = fetch_closing_quote("2330.TW")
print(quote.date, quote.code, quote.name, quote.close)
```

Batch adapters are also available:

```python
from taiwan_market_toolkit import fetch_tpex_closing_quotes, fetch_twse_closing_quotes

twse = fetch_twse_closing_quotes()
tpex = fetch_tpex_closing_quotes()
```

The common `ClosingQuote` model contains market, trading date, code, name, and closing price. Exchange-specific fields remain in the original official payload instead of being guessed into a shared schema.

## Official valuation metrics

```python
from taiwan_market_toolkit import find_valuation

metrics = find_valuation("2330.TW")
print(metrics.pe_ratio)
print(metrics.dividend_yield_pct)
print(metrics.price_to_book)
```

The same interface works for TPEx securities:

```python
metrics = find_valuation("6488.TWO")
```

Missing or non-calculated exchange values remain `None`. The toolkit does not turn valuation data into buy/sell recommendations.

## Trading calendar

```python
from datetime import date
from taiwan_market_toolkit import TaiwanTradingCalendar, fetch_twse_calendar

calendar = TaiwanTradingCalendar.from_overrides(
    closures=[date(2026, 1, 1)],
    openings=[],
)

print(calendar.next_trading_day(date(2026, 1, 1)))

official_twse = fetch_twse_calendar()
print(official_twse.is_trading_day(date(2026, 8, 11)))
```

The TWSE provider uses the official holiday schedule instead of shipping a copied holiday table that can silently go stale. A verified TPEx holiday adapter remains tracked separately until a stable authoritative machine-readable source is selected.

## Taiwan-style OHLCV input

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

English aliases, explicit column mappings, CSV input, and pandas-like DataFrames are supported without making pandas a mandatory dependency.

## Validation and descriptive analytics

```python
from taiwan_market_toolkit import (
    daily_returns,
    simple_moving_average,
    summarize_ohlcv,
    validate_ohlcv,
)

issues = validate_ohlcv(rows)
summary = summarize_ohlcv(rows)
sma20 = simple_moving_average(rows, 20)
returns = daily_returns(rows)
```

Moving averages and returns are data transformations only. They do not generate trading signals.

## Reproducible local snapshots

Current-state APIs can change after a research run. The toolkit can preserve the exact official closing response locally:

```bash
tw-market archive-quotes --market TWSE --root market-data
tw-market archive-quotes --market TPEX --root market-data
```

The archive stores source/date paths, preserves exact JSON bytes, records SHA-256 digests, treats identical writes as idempotent, and refuses to silently replace changed content for an already archived source/date. See `docs/snapshots.md`.

## CLI

```bash
tw-market symbol 2330.TW
tw-market company 2330.TW
tw-market search-company 台積
tw-market quote 2330.TW
tw-market valuation 2330.TW
tw-market calendar 2026-08-07 --next
tw-market validate examples/sample_ohlcv_zh.csv
tw-market analyze prices.csv --sma 5 --sma 20 --ema 20
```

Commands that query an exchange are read-only and require no brokerage credentials.

## MCP server

Install the optional dependency and run the local stdio server:

```bash
python -m pip install -e '.[mcp]'
tw-market-mcp
```

Current MCP tools include:

- `normalize_taiwan_symbol`
- `get_official_company_profile`
- `search_official_company_directory`
- `get_official_closing_quote`
- `get_official_valuation_metrics`
- `check_trading_day`
- `check_twse_trading_day`
- `validate_ohlcv_csv_text`
- `analyze_ohlcv_csv_text`

The MCP surface is intentionally read-only with respect to markets and excludes brokerage execution and private trading strategies.

## Official-source reliability

Normal CI uses compact fixtures instead of depending on live exchange uptime. A separate scheduled/manual smoke workflow probes implemented official TWSE/TPEx sources so schema drift and availability failures become visible.

Current official integrations include:

- TWSE listed-company basic data: `opendata/t187ap03_L`
- TPEx main-board company basic data: `mopsfin_t187ap03_O`
- TWSE closing snapshot: `exchangeReport/STOCK_DAY_ALL`
- TPEx closing snapshot: `tpex_mainboard_daily_close_quotes`
- TWSE valuation snapshot: `exchangeReport/BWIBBU_ALL`
- TPEx valuation snapshot: `tpex_mainboard_peratio_analysis`
- TWSE holiday schedule: `holidaySchedule/holidaySchedule`

See `docs/data-sources.md` for provenance, caching, and failure-behavior rules.

## Packaging and releases

Pull requests build and validate a wheel and source distribution. A PyPI Trusted Publishing workflow is present, but the first public release is intentionally gated on the release checklist in `docs/releasing.md` rather than being published just to create activity.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md`, `docs/architecture.md`, and the issue templates before opening a pull request. Do not submit proprietary datasets, brokerage credentials, private trading strategies, or data that cannot legally be redistributed.

## License

MIT License. See `LICENSE`.
