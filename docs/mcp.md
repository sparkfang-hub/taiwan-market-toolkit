# MCP server

Taiwan Market Toolkit includes an optional read-only Model Context Protocol server for AI hosts. The MCP layer wraps the same tested public market-data functions used by Python and the CLI; it is not a second implementation of market logic.

## Install

MCP dependencies are optional:

```bash
python -m pip install -e '.[mcp]'
```

Run the local stdio server:

```bash
tw-market-mcp
```

The core package does not require the MCP SDK unless this extra is installed.

## Current tools

The server currently exposes tools for:

- Taiwan ticker normalization;
- official TWSE/TPEx company profile lookup and directory search;
- official closing-price lookup;
- bounded joined market-snapshot queries;
- bounded official historical-price queries for the supported common-equity scope;
- official valuation metrics;
- a combined official security overview;
- generic trading-day checks with explicit overrides;
- official TWSE holiday-calendar checks;
- OHLCV CSV normalization and validation;
- strategy-neutral OHLCV summaries, returns, SMA, and EMA calculations.

Tool names are visible from the MCP host and include `normalize_taiwan_symbol`, `get_official_company_profile`, `search_official_company_directory`, `get_official_closing_quote`, `query_official_market_snapshot`, `get_official_price_history`, `get_official_valuation_metrics`, `get_official_security_overview`, `check_trading_day`, `check_twse_trading_day`, `validate_ohlcv_csv_text`, and `analyze_ohlcv_csv_text`.

## Bounded queries

AI-facing market-data tools use stricter limits than the underlying Python API.

Historical-price MCP requests are limited to at most 24 calendar months and at most 1,000 returned rows per call. Market-snapshot MCP queries are capped at 100 returned rows and report whether results were truncated.

These limits serve two purposes: they keep AI context sizes predictable and prevent a small natural-language request from becoming an accidental unbounded crawl of public exchange services.

For larger research jobs, use the Python API or CLI and cache official historical responses locally.

## Safety boundary

The MCP server is read-only with respect to markets and accounts. It does not expose:

- brokerage login or account access;
- order placement or cancellation;
- private trading strategies or security-selection rules;
- portfolio recommendations;
- autonomous buy/sell decisions.

No brokerage credential is required for the supported official public-data tools.

## Source and date semantics

MCP responses preserve the same source semantics as the core package. In particular, joined security/market snapshots do not invent a single shared timestamp when the official quote and valuation datasets were published for different dates.

Missing source values remain missing rather than being converted to zero. Historical observations remain unadjusted unless a future explicitly documented adjustment layer is requested through a separate public API.

See `data-sources.md`, `market-snapshots.md`, `historical-prices.md`, and `architecture.md` for the corresponding core behavior.

## Development

MCP contract tests use the installed optional SDK but monkeypatch network-backed functions where appropriate so ordinary CI stays deterministic.

```bash
python -m pip install -e '.[dev]'
pytest tests/test_mcp_server.py tests/test_mcp_market.py
```

When adding a new MCP tool, put reusable logic in a normal toolkit module first. The MCP registration should remain a thin adapter around that tested function, and any AI-facing range/result limit should be explicit.
