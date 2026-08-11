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
- OHLCV validation for price invariants, volume, duplicates, and ordering.
- Command-line interface for symbol, calendar, and CSV validation utilities.
- Optional MCP server using the official MCP Python SDK v2.
- MCP tools for symbol normalization, trading-day checks, and OHLCV CSV validation.
- Automated tests and GitHub Actions CI across Python 3.10-3.12.
- Contribution guidelines and data-source policy.
