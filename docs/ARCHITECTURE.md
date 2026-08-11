# Architecture

Taiwan Market Toolkit is intentionally split into small layers so reusable market infrastructure stays independent from private trading strategies.

## Design principles

1. **Core first, integrations second.** Core symbol, calendar, normalization, and validation behavior should remain deterministic and easy to test.
2. **External data has provenance.** Network-backed adapters document their authoritative source and keep fetching separate from parsing so callers can cache exact responses.
3. **Minimal mandatory dependencies.** The core package uses the Python standard library. Larger integrations such as MCP remain optional extras.
4. **No strategy layer.** The project does not implement buy/sell signals, portfolio selection, brokerage execution, account credentials, or private strategy parameters.
5. **AI interfaces wrap stable functions.** MCP tools should expose existing reusable capabilities rather than becoming a second implementation of market logic.

## Modules

### `symbols.py`

Normalizes Taiwan security identifiers and market suffix conventions. This module should stay free of network access.

### `calendar.py`

Provides the shared `TaiwanTradingCalendar` model. Weekends are handled locally; authoritative providers can supply explicit closures and openings.

### `twse.py`

Integrates the official Taiwan Stock Exchange OpenAPI holiday schedule. Fetching and parsing are separate to support caching, fixtures, and reproducible research.

### `validation.py`

Defines the canonical `OHLCVRow` and performs data-quality checks without making economic or trading judgments.

### `normalize.py`

Converts records, CSV input, and pandas-like objects into canonical OHLCV rows. Data-source-specific behavior should not be added here.

### `cli.py`

Provides thin command-line wrappers around stable public APIs.

### `mcp_server.py`

Optional MCP surface for AI hosts. It is read-only with respect to markets and accounts, has no brokerage access, and should remain a thin wrapper around tested toolkit functions.

## Data-flow example

A typical market-data workflow should look like:

1. fetch data from an external source in a source-specific adapter;
2. preserve or cache the raw response when reproducibility matters;
3. normalize rows into `OHLCVRow` values;
4. validate structural/data-quality invariants;
5. hand clean rows to the caller's own research or strategy layer outside this repository.

This boundary is deliberate: reusable infrastructure belongs here; proprietary decision logic does not.
