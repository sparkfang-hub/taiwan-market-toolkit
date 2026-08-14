# Taiwan Market Toolkit command map

Choose the smallest interface that answers the request. Network-backed commands use official public TWSE or TPEx sources implemented by the toolkit.

## Symbol and company identity

Normalize a ticker:

```bash
tw-market symbol 2330.TW
tw-market symbol 6488.TWO
```

Fetch one official company profile:

```bash
tw-market company 2330.TW
tw-market company 6488.TWO
```

Search the official company directory:

```bash
tw-market search-company 台積 --market TWSE --limit 10
tw-market search-company 環球晶 --market TPEX --limit 10
```

## Closing price, valuation, and combined overview

Latest official closing observation:

```bash
tw-market quote 2330.TW
```

Official valuation metrics:

```bash
tw-market valuation 2330.TW
```

Company identity, closing quote, and valuation in one response:

```bash
tw-market overview 2330.TW
```

Keep quote and valuation dates separate when they differ.

## Market-wide snapshot

Source-coverage summary only:

```bash
tw-market market-snapshot --summary-only
```

One exchange only:

```bash
tw-market market-snapshot --market TWSE --summary-only
tw-market market-snapshot --market TPEX --summary-only
```

Export normalized rows:

```bash
tw-market market-snapshot --output market-data/taiwan-equities.csv
```

Do not use the market snapshot to invent valuation rankings or recommendations. The joined view is identity- and source-oriented.

## Historical prices

Fetch a bounded range of official unadjusted daily history:

```bash
tw-market history 2330.TW --start 2026-01-01 --end 2026-08-11
```

Reuse exact completed-month source payloads during repeated research:

```bash
tw-market history 2330.TW --start 2026-01-01 --end 2026-08-11 --cache-dir market-cache/history
```

Export normalized history:

```bash
tw-market history 6488.TWO --start 2026-01-01 --end 2026-08-11 --output data/6488.csv
```

Historical rows are unadjusted. Do not infer corporate-action adjustments from price discontinuities.

## Corporate actions

Use the Python API until a dedicated CLI adapter is available:

```python
from datetime import date

from taiwan_market_toolkit import find_corporate_actions

rows = find_corporate_actions(
    "2330.TW",
    start=date(2026, 1, 1),
    end=date(2026, 12, 31),
)

for row in rows:
    print(
        row.date,
        row.kind.value,
        row.cash_dividend_per_share,
        row.stock_dividend_ratio,
        row.source,
    )
```

For market-wide or locally filtered work, reuse `fetch_corporate_actions` and `filter_corporate_actions` rather than scraping the exchange separately.

Pending or unpublished values remain `None`; a published zero remains zero.

## Trading calendar

Check a lightweight weekday-based date:

```bash
tw-market calendar 2026-08-11
```

Find the next or previous trading day:

```bash
tw-market calendar 2026-08-11 --next
tw-market calendar 2026-08-11 --previous
```

When official TWSE holiday semantics are required from Python, use `fetch_twse_calendar`. Do not claim a verified TPEx holiday provider until the toolkit adds one.

## OHLCV normalization and descriptive analytics

Normalize and validate a local CSV:

```bash
tw-market validate examples/sample_ohlcv_zh.csv
```

Calculate strategy-neutral summaries and moving averages:

```bash
tw-market analyze prices.csv --sma 5 --sma 20 --ema 20
```

The toolkit understands common Traditional Chinese OHLCV headers and common ROC-calendar date forms.

## Reproducible source capture

Archive the exact current official closing response with SHA-256 metadata:

```bash
tw-market archive-quotes --market TWSE --root market-data
tw-market archive-quotes --market TPEX --root market-data
```

## Response rules

Always distinguish official source values from locally computed analytics.

Preserve exchange observation dates, especially when quote and valuation datasets have different dates.

Report missing values as missing, not as zero.

If an official endpoint fails, report the source failure. Do not silently switch to an unrelated vendor.

Do not request credentials or cross the toolkit's read-only boundary into brokerage access, order execution, private strategy disclosure, or autonomous trading.