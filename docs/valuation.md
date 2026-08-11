# Official valuation metrics

Taiwan Market Toolkit exposes a small common valuation model over official TWSE and TPEx daily market datasets.

## Official sources

TWSE:

```text
https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL
```

TPEx main board:

```text
https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis
```

The source schemas use different field names, so exchange-specific parsing stays at the adapter boundary.

## Common model

`ValuationMetrics` contains:

- market
- trading date
- security code
- security name
- P/E ratio
- dividend yield percentage
- price-to-book ratio
- dividend per share when the source provides it

Missing or non-calculated values remain `None`. Strings such as an empty value or exchange no-value marker are not coerced to zero.

## Python API

```python
from taiwan_market_toolkit import find_valuation

metrics = find_valuation("2330.TW")
print(metrics.pe_ratio)
print(metrics.dividend_yield_pct)
print(metrics.price_to_book)
```

For a bare code, supply the market explicitly:

```python
metrics = find_valuation("6488", "TPEX")
```

Batch fetches are available as `fetch_twse_valuation`, `fetch_tpex_valuation`, and `fetch_valuation_metrics`.

## CLI

```bash
tw-market valuation 2330.TW
tw-market valuation 6488 --market TPEX
```

The command prints JSON and does not interpret the values as cheap, expensive, attractive, or unattractive.

## MCP

The optional MCP server exposes `get_official_valuation_metrics`. This is a read-only data tool. It does not generate buy/sell recommendations or combine the metrics with private strategy rules.

## Reliability boundary

Network fetch and parsing are separate. Normal tests use fixtures, while the scheduled official-source smoke workflow checks that both live exchange datasets continue to return parseable rows.

The common model is intentionally narrow. Metrics should only be added when the source meaning is clear enough to preserve without inventing cross-exchange equivalence.
