# Joined market snapshots

`MarketSnapshotRow` provides a batch view of listed Taiwan equities by joining three existing official source families:

- company identity from the TWSE or TPEx company directory;
- the latest official closing snapshot;
- the latest official valuation snapshot.

The company directory defines the row universe. Quote and valuation feeds are left-joined by `(market, code)` and cannot add extra rows on their own. This matters because exchange-wide quote feeds can include security types that are outside the toolkit's company-directory equity model.

## Python

Fetch both TWSE and TPEx listed-company snapshots:

```python
from taiwan_market_toolkit import fetch_market_snapshot

rows = fetch_market_snapshot()
```

Fetch only one market:

```python
rows = fetch_market_snapshot("TWSE")
```

Each row includes company identity plus the independently dated market observations:

```python
row = rows[0]
print(row.market, row.code, row.short_name)
print(row.quote_date, row.close)
print(row.valuation_date, row.pe_ratio, row.price_to_book)
```

`quote_date` and `valuation_date` are intentionally separate. The toolkit does not assume that exchange feeds are always published for the same effective date.

## Coverage summary

Use `summarize_market_snapshot()` to see whether every company-directory row matched the current quote and valuation feeds:

```python
from taiwan_market_toolkit import summarize_market_snapshot

summary = summarize_market_snapshot(rows)
print(summary.rows)
print(summary.missing_quote)
print(summary.missing_valuation)
print(summary.quote_dates)
print(summary.valuation_dates)
```

A missing source row is not the same thing as a published metric whose value is unavailable. For example, a company may have a valuation row with `pe_ratio=None`. In that case `has_valuation` remains true because the source row existed and explicitly lacked a calculated P/E value.

## CLI

Write a combined TWSE and TPEx CSV:

```bash
tw-market market-snapshot --output market-data/taiwan-equities.csv
```

Write only TWSE:

```bash
tw-market market-snapshot \
  --market TWSE \
  --output market-data/twse-equities.csv
```

Print only coverage information without embedding every company row:

```bash
tw-market market-snapshot --summary-only
```

Without `--output` or `--summary-only`, the command prints a JSON object containing the coverage summary plus all joined rows.

## Join and failure rules

The implementation deliberately follows these rules:

1. The official company directory is the listed-equity universe.
2. Closing and valuation datasets are joined only by exact market and security code.
3. Duplicate source keys raise an error instead of silently picking one row.
4. A listed company with no matching quote or valuation remains in the result with explicit `None` fields.
5. Source dates are preserved independently and are never rewritten to make the snapshot look synchronized.
6. The joined snapshot does not create trading signals, recommendations, rankings, or portfolio actions.

This design makes the batch view suitable as a clean infrastructure input for research systems while keeping strategy logic outside the public toolkit.
