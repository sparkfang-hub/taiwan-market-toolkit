# Changelog

All notable changes to this project will be documented here.

## Unreleased

### Added

- Initial Python package structure.
- Taiwan stock symbol normalization for TWSE and TPEx suffix conventions.
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
- Command-line interface for symbol, quote, local archiving, calendar, CSV validation, and descriptive analysis utilities.
- Optional MCP server using the official MCP Python SDK v2.
- MCP tools for official closing quotes, symbol normalization, trading-day checks, OHLCV CSV validation, and descriptive analytics.
- Runnable examples for Chinese CSV input, TWSE calendar queries, local snapshot archiving, and MCP clients.
- PyPI Trusted Publishing workflow and a documented release checklist.
- Distribution build and metadata validation in CI.
- Automated tests and GitHub Actions CI across Python 3.10-3.12.
- Contribution guidelines, architecture notes, security policy, and data-source policy.

### Changed

- GitHub Actions CI now uses Node 24-compatible `checkout` and `setup-python` actions.
- Package metadata now includes repository, issue tracker, and changelog URLs for public distribution.
