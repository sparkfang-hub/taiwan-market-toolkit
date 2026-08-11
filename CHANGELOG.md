# Changelog

All notable changes to this project will be documented here.

## Unreleased

### Added

- Initial Python package structure.
- Taiwan stock symbol normalization for TWSE and TPEx suffix conventions.
- Lightweight trading-calendar helpers with explicit closure/opening support.
- Official TWSE OpenAPI holiday-schedule provider and ROC-date parsing.
- OHLCV normalization for records, CSV input, and pandas-like DataFrames.
- Automatic common-column alias inference plus explicit column mapping.
- Traditional Chinese OHLCV column aliases for common Taiwan-market CSV schemas.
- ROC-calendar date support for normalized OHLCV records and CSV input.
- OHLCV validation for price invariants, volume, duplicates, and ordering.
- Strategy-neutral OHLCV analytics: SMA, EMA, one-period returns, summaries, and trading-day gap detection.
- Command-line interface for symbol, calendar, CSV validation, and descriptive analysis utilities.
- Optional MCP server using the official MCP Python SDK v2.
- MCP tools for symbol normalization, trading-day checks, OHLCV CSV validation, and descriptive analytics.
- Runnable examples for Chinese CSV input, TWSE calendar queries, and MCP clients.
- PyPI Trusted Publishing workflow and a documented release checklist.
- Distribution build and metadata validation in CI.
- Automated tests and GitHub Actions CI across Python 3.10-3.12.
- Contribution guidelines, architecture notes, security policy, and data-source policy.

### Changed

- GitHub Actions CI now uses Node 24-compatible `checkout` and `setup-python` actions.
- Package metadata now includes repository, issue tracker, and changelog URLs for public distribution.
