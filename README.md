# Taiwan Market Toolkit

Open-source Python infrastructure for working with public Taiwan stock-market data from TWSE and TPEx.

Taiwan-market datasets have details that generic market libraries often leave to every downstream application: `.TW`/`.TWO` symbols, ROC-calendar dates, Traditional Chinese CSV headers, exchange-specific company schemas, independently dated market snapshots, monthly historical pages, corporate-action announcements, valuation fields, and trading calendars. Taiwan Market Toolkit puts those edges behind small, testable APIs that can be reused by research pipelines, data-quality jobs, command-line tools, and AI agents.

This project is infrastructure, not a trading strategy. It deliberately excludes private signals, brokerage credentials, portfolio recommendations, and order execution.

For a short end-to-end walkthrough, start with `docs/quickstart.md`. For AI-agent workflows, see `docs/agent-skill.md`; the repository includes a `taiwan-market-research` Agent Skill that routes natural-language research tasks to the same tested CLI and Python APIs.

## Current capabilities

- Normalize TWSE/TPEx tickers and market aliases.
- Fetch and search a unified company directory from official TWSE and TPEx basic-data sources.
- Fetch official closing snapshots for TWSE and TPEx main-board securities.
- Join the official company universe, closing quotes, and valuation metrics into a market-wide snapshot while preserving independent source dates.
- Filter market snapshots by identity, market, industry code, and source coverage without creating investment rankings.
- Fetch official monthly daily-price history for ordinary four-digit TWSE/TPEx common equities.
- Cache completed historical months as exact official response bytes with SHA-256 verification.
- Fetch common official valuation metrics: P/E ratio, dividend yield, and price-to-book ratio.
- Normalize current official TWSE/TPEx ex-rights and ex-dividend announcements into a common corporate-action model.
- Query a Taiwan trading calendar with explicit closure/opening overrides and the official TWSE holiday schedule.
- Normalize OHLCV records, CSV files, and pandas-like DataFrames.
- Recognize common Traditional Chinese headers such as `交易日期`, `開盤價`, `最高價`, `最低價`, `收盤價`, and `成交股數`.
- Parse Gregorian and common ROC-calendar dates such as `115/08/11` and `1150811`.
- Validate OHLCV price invariants, volume, duplicates, and ordering.
- Calculate strategy-neutral SMA, EMA, one-period returns, summaries, and missing trading dates.
- Preserve exact official closing-snapshot JSON locally with SHA-256 integrity metadata.
- Expose bounded, read-only market utilities through an optional MCP server.
- Provide a repository-scoped Agent Skill for source-aware Taiwan market research through Codex and compatible skill hosts.
- Test on Python 3.10, 3.11, and 3.12, validate distributions, and smoke-test built wheels on Linux, macOS, and Windows.
- Run separate scheduled smoke checks against official exchange sources while keeping ordinary unit tests deterministic.

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

See `docs/quickstart.md` for a five-minute path through company data, market snapshots, historical prices, corporate actions, Taiwan-style CSV input, and MCP.

## Agent Skill

The repository includes `.agents/skills/taiwan-market-research/SKILL.md`. Codex can discover the skill when working in this repository, and the standalone skill can be installed from GitHub with the Codex skill installer.

The skill does not implement a second market-data stack. It maps user intent to existing commands and public APIs while preserving source dates, missing values, unadjusted-history semantics, and the project's read-only boundary.

Example request:

```text
Use Taiwan Market Toolkit to show the official company, closing-price, and valuation overview for 2330.TW. Keep the source dates separate.
```

See `docs/agent-skill.md` for installation details and more examples.

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

## Joined market snapshots

Build a current cross-source view of the listed-company universe:

```python
from taiwan_market_toolkit import fetch_market_snapshot, summarize_market_snapshot

rows = fetch_market_snapshot()
summary = summarize_market_snapshot(rows)
print(summary.rows, summary.missing_quote, summary.missing_valuation)
```

The company directory defines the row universe. Closing and valuation feeds are left-joined by exact market/code, so a missing daily source row remains visible rather than silently removing the company. Quote and valuation dates remain separate.

CLI:

```bash
tw-market market-snapshot --summary-only
tw-market market-snapshot --output market-data/taiwan-equities.csv
```

The library also provides deterministic identity/source-coverage filtering, and the MCP server exposes a bounded market-snapshot query tool. See `docs/market-snapshots.md`.

## Official historical prices

The exchange historical pages expose individual-security daily history one month at a time. The toolkit hides the month-by-month request loop, normalizes ROC dates and source fields, applies conservative pacing/retry behavior, and returns one common `HistoricalPrice` representation.

```python
from datetime import date
from taiwan_market_toolkit import fetch_price_history, history_to_ohlcv

prices = fetch_price_history(
    "2330.TW",
    start=date(2026, 1, 1),
    end=date(2026, 8, 11),
    cache_dir="market-cache/history",
)

rows = history_to_ohlcv(prices)
```

TPEx common-stock history labels volume in trading lots and trade value in thousands. For ordinary four-digit common equities, those quantities are normalized to shares and TWD. Non-four-digit products are rejected in v0.1 rather than silently applying the wrong trading-unit convention.

Completed months can be cached as exact official payload bytes with digest verification. The current month remains live because it can still change.

The historical adapter is intentionally unadjusted. It does not infer dividend, split, capital-reduction, or other corporate-action adjustments from price jumps. See `docs/historical-prices.md` for the full scope and reliability model.

## Corporate-action announcements

Current official TWSE and TPEx ex-rights/ex-dividend announcement tables can be normalized into one model:

```python
from taiwan_market_toolkit import fetch_corporate_actions

rows = fetch_corporate_actions()
for row in rows[:5]:
    print(
        row.date,
        row.market.value,
        row.code,
        row.kind.value,
        row.cash_dividend_per_share,
        row.stock_dividend_ratio,
    )
```

Pending exchange values remain `None`; a published numeric zero remains zero. The normalized model includes stock-dividend ratios, cash dividends, cash-capital-increase subscription terms, and related subscription fields when published.

This is an announcement-data layer, not an adjusted-price engine. Price-adjustment methodology remains intentionally separate. See `docs/corporate-actions.md`.

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
tw-market overview 2330.TW
tw-market corporate-actions --market TWSE --code 2330 --output market-data/corporate-actions.csv
tw-market market-snapshot --summary-only
tw-market market-snapshot --output market-data/taiwan-equities.csv
tw-market history 2330.TW --start 2026-01-01 --end 2026-08-11
tw-market history 6488.TWO --start 2026-01-01 --end 2026-08-11 --output data/6488.csv
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
- `query_official_market_snapshot`
- `get_official_price_history`
- `get_official_valuation_metrics`
- `get_official_security_overview`
- `check_trading_day`
- `check_twse_trading_day`
- `validate_ohlcv_csv_text`
- `analyze_ohlcv_csv_text`

Market-snapshot and historical queries have explicit response/range limits so an AI host cannot accidentally turn a small question into an unbounded exchange crawl or context dump. The MCP surface is intentionally read-only with respect to markets and excludes brokerage execution and private trading strategies.

## Official-source reliability

Normal CI uses compact fixtures instead of depending on live exchange uptime. A separate scheduled/manual smoke workflow probes implemented official TWSE/TPEx sources so schema drift and availability failures become visible.

Current official integrations include:

- TWSE listed-company basic data: `opendata/t187ap03_L`
- TPEx main-board company basic data: `mopsfin_t187ap03_O`
- TWSE closing snapshot: `exchangeReport/STOCK_DAY_ALL`
- TPEx closing snapshot: `tpex_mainboard_daily_close_quotes`
- TWSE individual historical prices: `exchangeReport/STOCK_DAY`
- TPEx individual main-board historical prices: `www/zh-tw/afterTrading/tradingStock`
- TWSE valuation snapshot: `exchangeReport/BWIBBU_ALL`
- TPEx valuation snapshot: `tpex_mainboard_peratio_analysis`
- TWSE ex-rights/ex-dividend announcements: `exchangeReport/TWT48U_ALL`
- TPEx ex-rights/ex-dividend announcements: `tpex_exright_prepost`
- TWSE holiday schedule: `holidaySchedule/holidaySchedule`

See `docs/data-sources.md` for provenance, caching, and failure-behavior rules.

## Packaging and maintenance

Pull requests run the Python 3.10-3.12 test matrix, build and validate wheel/source distributions, and install the built wheel on Linux, macOS, and Windows. Monthly dependency maintenance is configured for Python and GitHub Actions dependencies.

A PyPI Trusted Publishing workflow is present, but the first public release is intentionally gated on `docs/releasing.md` rather than being published simply to create activity. Maintainer triage, upstream-source incidents, compatibility expectations, and release handling are documented in `docs/maintaining.md`.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md`, `docs/architecture.md`, and the issue templates before opening a pull request. Do not submit proprietary datasets, brokerage credentials, private trading strategies, or data that cannot legally be redistributed.

For reproducible source/parser bugs, the most useful report includes the exchange, endpoint, Python version, operating system, and the smallest redistributable example that demonstrates the problem.

## License

MIT License. See `LICENSE`.
