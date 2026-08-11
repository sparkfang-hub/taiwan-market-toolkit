# Official historical prices

Taiwan Market Toolkit can fetch monthly daily-price history for ordinary four-digit Taiwan common equities from the official exchange websites.

## Supported sources

TWSE uses the official `exchangeReport/STOCK_DAY` historical daily-trading endpoint. The TWSE historical page states that this daily trading dataset is available from 2010-01-04 onward.

TPEx uses the official `www/zh-tw/afterTrading/tradingStock` historical main-board endpoint. The TPEx historical page states that individual main-board history is available from 1994-01 onward.

The toolkit requests one calendar month at a time because that is the natural unit exposed by both official services.

## Python

```python
from datetime import date

from taiwan_market_toolkit import fetch_price_history, history_to_ohlcv

prices = fetch_price_history(
    "2330.TW",
    start=date(2026, 1, 1),
    end=date(2026, 8, 11),
)

rows = history_to_ohlcv(prices)
```

Bare tickers require an explicit market:

```python
prices = fetch_price_history(
    "6488",
    "TPEX",
    start=date(2026, 1, 1),
    end=date(2026, 8, 11),
)
```

## Exact monthly response cache

Repeatedly downloading completed historical months wastes public exchange capacity and makes research less reproducible. Supply `cache_dir` to preserve the exact official JSON response bytes for each market/security/month:

```python
prices = fetch_price_history(
    "2330.TW",
    start=date(2025, 1, 1),
    end=date(2026, 8, 11),
    cache_dir="market-cache/history",
)
```

The cache layout is deterministic:

```text
market-cache/history/twse/2330/2025/2025-01.json
market-cache/history/twse/2330/2025/2025-01.json.sha256
```

Completed months are reused on later calls. The current calendar month is always requested again because the official response is still changing. Use `refresh=True` to deliberately bypass completed-month cache entries.

The SHA-256 sidecar is checked when a cached payload is read. A digest mismatch fails visibly rather than quietly feeding corrupted bytes into research. Changed bytes for an already cached completed month are not silently overwritten unless the caller explicitly refreshes.

The cache stores raw response bytes, not pickled Python objects or a transformed proprietary format. Parsing remains separate, which makes the source evidence inspectable and allows future parser improvements to be applied to the same captured response.

## CLI

Print normalized JSON:

```bash
tw-market history 2330.TW --start 2026-01-01 --end 2026-08-11
```

Reuse completed monthly responses locally:

```bash
tw-market history 2330.TW \
  --start 2025-01-01 \
  --end 2026-08-11 \
  --cache-dir market-cache/history
```

Force a refresh when you intentionally want to check for official revisions:

```bash
tw-market history 2330.TW \
  --start 2025-01-01 \
  --end 2025-12-31 \
  --cache-dir market-cache/history \
  --refresh
```

Write normalized CSV:

```bash
tw-market history 2330.TW \
  --start 2026-01-01 \
  --end 2026-08-11 \
  --output data/2330-history.csv
```

## MCP

The optional MCP server exposes `get_official_price_history`. The AI-facing surface is deliberately bounded to at most 24 calendar months and at most 1,000 returned rows per call. This prevents an agent from accidentally turning a simple question into an unbounded crawl of a public exchange service.

The MCP tool does not choose a local cache directory on behalf of the host. Applications that want persistent caching should call the Python API or CLI with an explicit storage policy.

## Common model

Each `HistoricalPrice` preserves:

- market and security code;
- trading date;
- open, high, low, and close;
- normalized share volume;
- normalized trade value;
- daily change;
- transaction count;
- source identifier.

Official missing OHLC values are kept as `None` rather than invented. `history_to_ohlcv()` skips incomplete observations by default; use `strict=True` if missing OHLC should fail a reproducibility run.

## TPEx units and v0.1 scope

The TPEx historical common-stock table labels volume as trading lots and trade value in thousands. For ordinary four-digit common equities, the adapter normalizes these values to shares and TWD by multiplying by 1,000.

Some exchange-traded products use different trading-unit conventions. To avoid silently producing incorrect comparable volume, the v0.1 historical adapter rejects non-four-digit symbols instead of guessing. A future product-aware adapter can add ETF, ETN, bond, and other security types with explicit unit metadata.

## Reliability and source etiquette

`fetch_price_history()` has conservative defaults:

- monthly requests are paced;
- temporary failures receive a small retry budget with backoff;
- a request spans at most 120 calendar months unless the caller deliberately changes the guard;
- completed months can reuse exact locally cached response bytes;
- the current month is refreshed instead of being treated as immutable history;
- parser/schema and cache-integrity failures remain visible rather than being converted to empty data;
- normal unit tests use fixtures and never depend on live exchange availability.

This project is not a bulk redistribution service. Applications that need large historical datasets should cache locally, respect official terms and service limits, and avoid repeatedly downloading unchanged months.

## Data interpretation

Historical rows are raw market observations, not adjusted total-return series. Corporate actions can create discontinuities. The toolkit does not currently back-adjust prices for dividends, splits, capital reductions, or other events.

That limitation is intentional: adjusted series should be built from explicit corporate-action data and documented methodology, not inferred from price jumps.
