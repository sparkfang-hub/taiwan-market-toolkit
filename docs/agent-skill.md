# Agent Skill

Taiwan Market Toolkit includes a repository-scoped Agent Skill for source-aware Taiwan market research.

The skill lives at `.agents/skills/taiwan-market-research/` and routes natural-language research requests to the toolkit's existing read-only CLI and Python APIs instead of duplicating market-data logic.

## What the skill covers

The skill is intended for official TWSE and TPEx company lookup, closing prices, valuation metrics, security overviews, market snapshots, historical prices, corporate-action announcements, trading-day checks, OHLCV validation, and descriptive analytics.

It preserves the toolkit's existing reliability rules: quote and valuation dates stay independent, missing values remain missing, historical prices remain unadjusted, and upstream source failures are reported instead of replaced with guessed values.

The skill does not add brokerage access, credentials, order execution, private trading strategies, or autonomous buy/sell decisions.

## Use inside this repository

Codex discovers repository skills under `.agents/skills`. When working from this repository, make the package available first:

```bash
python -m pip install -e .
```

Then ask for a Taiwan market research task naturally, or explicitly select the `taiwan-market-research` skill from the available skill list.

## Install the skill from GitHub

Codex can install standalone skills from GitHub repositories with its skill installer. Point the installer at:

```text
sparkfang-hub/taiwan-market-toolkit/.agents/skills/taiwan-market-research
```

The skill is intentionally small. It delegates data fetching and parsing to the versioned toolkit rather than embedding exchange scraping logic into the instruction file.

Outside a repository checkout, install the current development package directly from GitHub when your environment allows it:

```bash
python -m pip install "git+https://github.com/sparkfang-hub/taiwan-market-toolkit.git"
```

The project has not yet rushed a PyPI release, so the GitHub installation path remains the current external setup route.

## Example requests

```text
Use Taiwan Market Toolkit to show the official company, closing-price, and valuation overview for 2330.TW. Keep the source dates separate.
```

```text
Use Taiwan Market Toolkit to fetch official unadjusted daily history for 6488.TWO from 2026-01-01 through 2026-08-11 and summarize the latest 20-day SMA.
```

```text
Use Taiwan Market Toolkit to find current official corporate-action announcements for 2330.TW and distinguish missing values from published zero values.
```

```text
Use Taiwan Market Toolkit to check market-snapshot source coverage without ranking stocks or giving a recommendation.
```

## Design principle

The Agent Skill is a distribution and orchestration layer, not a second market-data implementation. New exchange adapters, normalization rules, and calculations belong in tested Python modules first. The skill should remain a thin map from user intent to those public interfaces.

OpenAI's current Agent Skills documentation defines the skill instruction file as the required entry point and supports repository-scoped discovery under `.agents/skills`. Skills can also be installed from repositories through the skill installer. For broader distribution, OpenAI documents Plugins as the packaging layer for skills and related resources.
