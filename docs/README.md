# Documentation

Use this index to find the shortest path for a task.

## Start here

- `quickstart.md` — install the development version and try the main Python, CLI, and MCP workflows.
- `architecture.md` — understand module boundaries, data flow, reproducibility, and the strategy boundary.
- `data-sources.md` — see official TWSE/TPEx endpoints, provenance, normalization assumptions, and failure rules.

## Market data

- `company-directory.md` — unified TWSE/TPEx listed-company identity data.
- `market-snapshots.md` — joined company, closing-price, and valuation snapshots plus deterministic filtering.
- `historical-prices.md` — official monthly history, source units, request pacing, exact-byte caching, and scope limitations.
- `corporate-actions.md` — normalized ex-rights/ex-dividend announcement inputs and the boundary before adjusted-price methodology.
- `valuation.md` — common official P/E, dividend-yield, and price-to-book metrics.
- `snapshots.md` — exact current-response archives and SHA-256 integrity metadata.

## Interfaces

- `mcp.md` — optional read-only MCP server for AI hosts.
- The root `README.md` lists the current CLI commands and public package capabilities.

## Project maintenance

- `maintaining.md` — pull-request review, issue triage, upstream-source incidents, dependency maintenance, and release handling.
- `releasing.md` — first-release prerequisites, PyPI Trusted Publishing, and release verification.
- Root `CONTRIBUTING.md` — development setup and contribution requirements.
- Root `SECURITY.md` — vulnerability reporting and security boundaries.

## Design stance

The repository focuses on reusable Taiwan market-data infrastructure. It deliberately keeps brokerage credentials, order execution, private security-selection rules, portfolio recommendations, and private trading strategies outside the public package.
