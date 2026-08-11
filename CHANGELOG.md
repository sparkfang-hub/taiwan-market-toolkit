# Changelog

All notable changes to this project will be documented here.

## Unreleased

### Added

- Initial Python package structure.
- Taiwan stock symbol normalization for TWSE and TPEx suffix conventions.
- Unified official TWSE/TPEx `SecurityProfile` company directory with local code/name search.
- `tw-market company` and `tw-market search-company` commands for official company identity metadata.
- Read-only official TWSE/TPEx valuation adapters with a common `ValuationMetrics` model for P/E ratio, dividend yield, and price-to-book ratio.
- `tw-market valuation` command and MCP valuation tool.
- `SecurityOverview` convenience layer combining official company identity, closing quote, and valuation data while preserving independent source dates.
- `tw-market overview` command and `get_official_security_overview` MCP tool.
- Unified `MarketSnapshotRow` batch view that left-joins the official company universe with closing quotes and valuation metrics while preserving independent source dates.
- Market-snapshot coverage summaries that make missing quote or valuation rows explicit instead of dropping listed companies.
- `filter_market_snapshot` for deterministic code/name, market, industry, and source-coverage filtering without investment ranking logic.
- `tw-market market-snapshot` command with both-market or single-market selection, JSON summaries, and UTF-8 CSV export.
- Bounded `query_official_market_snapshot` MCP tool with identity/source filtering and a 100-row response cap.
- Official monthly TWSE/TPEx historical daily-price adapters for ordinary four-digit common equities.
- Common `HistoricalPrice` model with source, OHLC, normalized share volume, trade value, change, and transaction count.
- Conservative monthly historical fetching with pacing, retry/backoff, request-span guards, and date-range filtering.
- Exact-byte historical response cache with deterministic market/security/month paths and SHA-256 verification.
- Completed-month cache reuse plus explicit refresh behavior while keeping the current month live.
- Raw TWSE/TPEx historical response fetchers so caching and parsing remain separate.
- `history_to_ohlcv` integration so official exchange history can feed the existing validation and analytics pipeline.
- `tw-market history` command with JSON output or normalized UTF-8 CSV export.
- `tw-market history --cache-dir` and `--refresh` controls for reproducible, source-friendly history workflows.
- Bounded `get_official_price_history` MCP tool with 24-month and 1,000-row safety limits.
- Runnable official-history example that feeds the returned rows into SMA calculation.
- Lightweight trading-calendar helpers with explicit closure/opening support.
- Official TWSE OpenAPI holiday-schedule provider and ROC-date parsing.
- Read-only TWSE and TPEx official closing-quote adapters with a common `ClosingQuote` model.
- Raw TWSE/TPEx closing-response fetchers for reproducible caching workflows.
- Local `SnapshotStore` that preserves exact JSON bytes by source/date with SHA-256 metadata.
- `tw-market quote` CLI command for one official latest closing snapshot.
- `tw-market archive-quotes` CLI command for locally preserving official closing snapshots.
- Scheduled/manual GitHub Actions smoke checks for implemented official exchange sources.
- OHLCV normalization for records, CSV input, and pandas-like DataFrames.
- Automatic common-column alias inference plus explicit column mapping.
- Traditional Chinese OHLCV column aliases for common Taiwan-market CSV schemas.
- ROC-calendar date support for normalized OHLCV records and CSV input.
- OHLCV validation for price invariants, volume, duplicates, and ordering.
- Strategy-neutral OHLCV analytics: SMA, EMA, one-period returns, summaries, and trading-day gap detection.
- Command-line interface for company lookup/search, symbol, quote, valuation, overview, market snapshots, historical prices, local archiving, calendar, CSV validation, and descriptive analysis utilities.
- Optional MCP server using the official MCP Python SDK v2.
- MCP tools for official security overview, company profiles/search, closing quotes, bounded market-snapshot queries, bounded historical prices, valuation metrics, symbol normalization, trading-day checks, OHLCV CSV validation, and descriptive analytics.
- Runnable examples for Chinese CSV input, TWSE calendar queries, official history, local snapshot archiving, and MCP clients.
- PyPI Trusted Publishing workflow and a documented release checklist.
- Distribution build and metadata validation in CI.
- Automated tests and GitHub Actions CI across Python 3.10-3.12.
- Contribution guidelines, architecture notes, security policy, and data-source policy.

### Changed

- GitHub Actions CI now uses Node 24-compatible `checkout` and `setup-python` actions.
- Package metadata now includes repository, issue tracker, and changelog URLs for public distribution.
- Historical TPEx normalization is deliberately scoped to four-digit common equities so non-equity trading-unit conventions are not guessed.
