# Five-minute quickstart

Taiwan Market Toolkit is an alpha-stage Python package for normalizing and querying public Taiwan market data from official TWSE and TPEx sources. The fastest way to try the current development version is from a local clone.

## 1. Install

Python 3.10, 3.11, and 3.12 are tested in CI. Built wheels are also smoke-tested on Linux, macOS, and Windows.

```bash
git clone https://github.com/sparkfang-hub/taiwan-market-toolkit.git
cd taiwan-market-toolkit
python -m pip install -e .
```

Optional MCP support:

```bash
python -m pip install -e '.[mcp]'
```

## 2. Inspect one listed company

```bash
tw-market company 2330.TW
tw-market quote 2330.TW
tw-market valuation 2330.TW
tw-market overview 2330.TW
```

The commands are read-only. No brokerage account, API key, or trading credential is required.

Bare tickers do not guess their exchange. Use `.TW` for TWSE, `.TWO` for TPEx, or pass an explicit market.

## 3. Build a current market snapshot

Fetch the current joined company/closing/valuation view for both exchanges and write it as UTF-8 CSV:

```bash
tw-market market-snapshot --output market-data/taiwan-equities.csv
```

Check source coverage without printing every row:

```bash
tw-market market-snapshot --summary-only
```

The company directory defines the listed-company universe. Quote and valuation data are left-joined, so missing source rows stay visible rather than silently removing a company.

## 4. Fetch official historical prices

```bash
tw-market history 2330.TW \
  --start 2026-01-01 \
  --end 2026-08-11 \
  --cache-dir market-cache/history \
  --output market-data/2330.csv
```

Completed historical months can be cached as exact exchange-response bytes with SHA-256 verification. The current month remains live because its source data can still change.

The historical adapter currently targets ordinary four-digit TWSE/TPEx common equities. It intentionally rejects products whose exchange trading-unit conventions have not yet been modeled explicitly.

## 5. Inspect corporate-action announcements

```python
from taiwan_market_toolkit import fetch_corporate_actions

rows = fetch_corporate_actions()
for row in rows[:10]:
    print(
        row.date,
        row.market.value,
        row.code,
        row.kind.value,
        row.cash_dividend_per_share,
        row.stock_dividend_ratio,
    )
```

The corporate-action layer normalizes current official ex-rights/ex-dividend announcement feeds. Pending exchange values remain missing rather than being guessed. Adjusted prices are a separate future methodology layer.

## 6. Work with Taiwan-style CSV files

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

print(rows[0])
```

Common Traditional Chinese headers and ROC-calendar dates are normalized into the shared OHLCV model.

## 7. Try the MCP server

```bash
tw-market-mcp
```

The optional MCP server exposes bounded, read-only market-data tools for AI hosts. It does not expose brokerage execution, private trading strategies, or order placement.

## What to read next

- `docs/data-sources.md` for official source provenance and failure behavior
- `docs/historical-prices.md` for history scope, units, caching, and limitations
- `docs/market-snapshots.md` for batch join semantics
- `docs/corporate-actions.md` for ex-rights/ex-dividend normalization
- `docs/architecture.md` for module boundaries
- `CONTRIBUTING.md` for contribution rules
- `docs/maintaining.md` for maintainer triage and release workflow

## Alpha expectations

The project is usable but still alpha. Public APIs can evolve before 1.0, and the first PyPI release is intentionally gated by the release checklist rather than being published simply to create activity. If you encounter a reproducible parsing or data-quality problem, opening a focused issue with the exchange, endpoint, Python version, and smallest redistributable example is the most useful feedback.
