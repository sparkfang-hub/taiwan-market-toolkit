# Architecture

Taiwan Market Toolkit is organized as small, source-aware layers so public Taiwan market-data infrastructure stays independent from downstream trading strategies and brokerage integrations.

## Design principles

1. Core transformations stay deterministic. Symbol normalization, calendar rules, parsing, joins, validation, and analytics should be testable without live network access.
2. External data carries provenance. Network-backed adapters document an official source and keep fetching separate from parsing whenever practical.
3. Missing information stays missing. The toolkit does not turn unavailable source values into zero or synchronize dates that were published independently.
4. Raw evidence can be preserved. Current and historical source payloads can be archived or cached when reproducibility matters.
5. Mandatory dependencies stay small. The core package uses the Python standard library; MCP is an optional extra.
6. AI interfaces wrap tested public functions. MCP tools should remain bounded adapters instead of implementing a parallel market-data stack.
7. Strategy stays outside the repository. The public package does not implement buy/sell signals, private ranking rules, portfolio recommendations, brokerage execution, account credentials, or private strategy parameters.

## Layers

### Identity and calendar

`symbols.py` normalizes Taiwan security identifiers, exchange aliases, and `.TW`/`.TWO` conventions without network access.

`calendar.py` provides the shared `TaiwanTradingCalendar` model. Weekends are handled locally; authoritative providers can supply explicit market closures and openings.

`twse.py` integrates the official TWSE holiday schedule. Fetching and parsing are separate so tests can use fixtures and applications can preserve source responses.

### Official company and market snapshots

`directory.py` normalizes the official TWSE listed-company and TPEx main-board company directories into `SecurityProfile` identity records.

`quotes.py` exposes the common subset of the official current closing snapshots as `ClosingQuote` while keeping raw-response fetching available for reproducible archives.

`valuation.py` normalizes common official P/E, dividend-yield, and price-to-book fields into `ValuationMetrics` without creating valuation judgments.

`overview.py` composes company identity, a closing quote, and valuation metrics for one security while preserving independently published source dates.

`market_snapshot.py` builds a batch listed-company view by left-joining the official company universe with closing and valuation snapshots by exact `(market, code)`. Source feeds cannot silently add unrelated security types to the company universe, and missing source rows remain explicit.

`market_query.py` provides deterministic filtering over already-built market snapshots. Filtering is identity/source-coverage oriented and deliberately avoids financial ranking or security selection logic.

### Historical prices and reproducibility

`history.py` fetches and parses monthly official TWSE/TPEx historical daily-price sources for the currently supported common-equity scope. It normalizes ROC dates, source fields, and supported exchange units into `HistoricalPrice` while preserving incomplete official OHLC observations.

`history_cache.py` preserves exact completed-month exchange-response bytes under deterministic paths with SHA-256 verification. The current month remains live because the official source can still change.

`snapshots.py` preserves exact current closing-snapshot payloads with source/date paths and digest metadata. Identical writes are idempotent; conflicting same-date bytes require explicit replacement.

### Corporate actions

`corporate_actions.py` normalizes current official TWSE/TPEx ex-rights and ex-dividend announcement feeds into `CorporateAction`. Published zero remains zero, pending/unannounced values remain missing, and the original exchange action label is retained.

This layer provides adjustment inputs only. It does not yet calculate adjusted historical prices or total-return series; those require an explicit reviewed methodology.

### OHLCV normalization, validation, and analytics

`validation.py` defines canonical `OHLCVRow` values and structural/data-quality checks without making economic judgments.

`normalize.py` converts records, Traditional Chinese/English CSV schemas, ROC/Gregorian dates, and pandas-like objects into canonical OHLCV rows. Data-source-specific fetching should not be added here.

`analytics.py` contains strategy-neutral descriptive transforms such as SMA, EMA, one-period returns, summaries, and trading-day gap detection.

### User interfaces

`cli.py` provides thin command-line wrappers around stable public APIs. Network-backed commands remain read-only with respect to markets and require no brokerage credentials.

`mcp_server.py` creates the optional MCP server. Specialized MCP registration can live in modules such as `mcp_market.py`, while reusable market logic remains in core modules first. AI-facing queries are bounded to avoid accidental large exchange crawls or context dumps.

## Data flow

A typical reproducible research path is:

1. resolve the security identity and market;
2. fetch an official source through a source-specific adapter;
3. preserve exact raw bytes when reproducibility matters;
4. parse and normalize into a narrow shared model;
5. validate structural or data-quality invariants;
6. perform strategy-neutral transforms such as summaries or moving averages;
7. hand the clean data to the caller's own research or strategy layer outside this repository.

A current market-wide path is similar:

1. fetch the official company directory as the listed-company universe;
2. fetch current official quote and valuation snapshots;
3. left-join by exact market/security code while preserving each source date;
4. inspect coverage and filter deterministically;
5. export to CSV, use the Python API, or expose a bounded MCP query.

## Source failures and schema drift

Ordinary unit tests use compact fixtures and do not depend on exchange uptime. Scheduled source-smoke jobs exercise implemented official endpoints independently. If an upstream schema changes, the intended response is to fail visibly, inspect the new official shape, add a regression fixture, and then update the parser. The project should not silently reinterpret renamed or missing fields.

See `docs/data-sources.md` for source provenance and `docs/maintaining.md` for the incident and review workflow.

## Release boundary

The package is currently alpha. Pull requests run the Python 3.10-3.12 test matrix, distribution validation, and built-wheel smoke installation on Linux, macOS, and Windows. The first PyPI release is gated by `docs/releasing.md` and the public release checklist rather than a commit-count target.

This boundary is deliberate: reusable, source-aware Taiwan market infrastructure belongs here; proprietary decision logic does not.
