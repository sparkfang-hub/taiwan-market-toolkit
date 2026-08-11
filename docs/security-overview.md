# Security overview

`SecurityOverview` composes three existing official-data adapters for one Taiwan security:

- company identity metadata;
- latest published closing quote;
- latest published valuation metrics.

It is a convenience layer, not a new data source.

## Python

```python
from taiwan_market_toolkit import fetch_security_overview

overview = fetch_security_overview("2330.TW")

print(overview.profile.short_name)
print(overview.quote.close)
print(overview.quote.date)
print(overview.valuation.pe_ratio)
print(overview.valuation.date)
```

Bare tickers require an explicit market:

```python
overview = fetch_security_overview("6488", "TPEX")
```

## Independent source dates

The overview deliberately keeps the closing-quote date and valuation date separate. Official datasets can be published or updated on different schedules. The toolkit does not collapse those dates into a single fake `as_of` value.

`SecurityOverview` also validates that profile, quote, and valuation components all refer to the same market and security code.

## CLI

```bash
tw-market overview 2330.TW
tw-market overview 6488 --market TPEX
```

The command returns nested JSON with `profile`, `quote`, and `valuation` sections so provenance and observation dates remain visible.

## MCP

The optional MCP server exposes `get_official_security_overview` with the same nested structure.

This surface is read-only. It does not calculate trade signals, combine the data with a private strategy, or execute orders.
