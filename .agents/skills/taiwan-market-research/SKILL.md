---
name: taiwan-market-research
description: Query and analyze official Taiwan stock-market data from TWSE and TPEx with taiwan-market-toolkit. Use for Taiwan ticker and company lookup, official closing prices, valuation metrics, security overviews, market snapshots, historical OHLCV, corporate actions, trading-day checks, and source-aware Taiwan market research. Do not use for brokerage access, order execution, private trading strategies, or buy/sell recommendations.
---

# Taiwan Market Research

Use Taiwan Market Toolkit as the source-aware, read-only interface for Taiwan stock-market research.

## Operating rules

Prefer the toolkit's tested CLI and Python API over ad hoc scraping or invented exchange mappings.

Before a network-backed query, make sure the toolkit is available. If `tw-market` is already installed, use it. When working inside a checkout of this repository, install with:

```bash
python -m pip install -e .
```

When working outside this repository and installation from GitHub is allowed, install with:

```bash
python -m pip install "git+https://github.com/sparkfang-hub/taiwan-market-toolkit.git"
```

If package installation or network access is unavailable, state the limitation and give the exact command the user can run instead of silently substituting an unrelated data provider.

## Choose the narrowest interface

Use `references/command-map.md` to map the user's intent to the smallest suitable CLI command or Python API.

Prefer one-security queries such as `overview`, `quote`, `valuation`, or `company` when the question is about one ticker. Use `market-snapshot` only for market-wide identity or source-coverage work. Use `history` only for a bounded date range and use `--cache-dir` for repeated historical research.

Corporate-action announcements currently use the Python API. Reuse `find_corporate_actions`, `fetch_corporate_actions`, and `filter_corporate_actions`; do not create a new scraper.

## Preserve source semantics

Treat exchange data as observations with source-specific dates. Do not collapse independently published quote and valuation dates into a fabricated shared timestamp.

Preserve missing values as missing. Do not convert `None` or an exchange no-value marker to numeric zero.

Historical prices are unadjusted unless an explicitly documented adjustment method is added later. Do not infer dividends, splits, capital reductions, or other corporate actions from price jumps.

For bare Taiwan tickers, require or infer a market only when the toolkit can do so safely. `.TW` means TWSE and `.TWO` means TPEx. Do not guess the exchange for an ambiguous bare ticker.

## Answering research questions

Run the most specific command or API call that answers the question. Prefer structured JSON output when using the CLI.

In the final answer, identify the security and market, report the relevant observation date or dates, distinguish official values from calculations performed locally, and call out missing or unavailable source data when material.

If the user requests a simple descriptive calculation such as an SMA, EMA, return, or OHLCV summary, use the toolkit's strategy-neutral analytics. Do not transform descriptive output into a buy, sell, ranking, portfolio, or execution instruction unless the user explicitly asks for general educational analysis that remains outside brokerage execution.

## Safety boundary

Never request brokerage credentials, API keys, cookies, account identifiers, or private trading rules for these workflows.

Do not place, cancel, simulate, or prepare orders. Do not claim the toolkit can access a brokerage account.

Do not fabricate official exchange values when an endpoint is unavailable or a schema has changed. Report the upstream failure and preserve the distinction between unavailable data and zero.