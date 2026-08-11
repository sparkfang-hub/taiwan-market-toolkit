# Contributing

Thanks for considering a contribution to Taiwan Market Toolkit.

Please read `CODE_OF_CONDUCT.md` before participating. For design boundaries and module responsibilities, see `docs/ARCHITECTURE.md`. Maintainers use the triage, source-incident, dependency, and release process documented in `docs/maintaining.md`.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Pull requests

1. Open an issue for larger changes before implementation.
2. Keep pull requests focused and add tests for behavior changes.
3. Do not include proprietary market data, API credentials, trading strategies, or data that cannot be redistributed.
4. Prefer small, composable utilities with clear public APIs.
5. Update documentation and `CHANGELOG.md` when adding or changing user-facing behavior.
6. Keep MCP tools thin and read-only with respect to brokerage/accounts; reusable market logic belongs in core modules first.
7. Wait for the Python test matrix, package validation, and cross-platform built-wheel smoke tests to pass before merge.

## Data-source policy

This project aims to provide reusable market-data tooling, not to redistribute data without permission. Contributions that integrate external sources should document the source, license or terms, update frequency, and failure behavior.

Network-backed integrations should keep fetching separate from parsing when practical. This makes tests deterministic and lets users cache exact source responses for reproducible research.

## Reporting bugs

Please include a minimal reproducible example, Python version, operating system, and the smallest sample data necessary to reproduce the issue.

For sensitive vulnerabilities, follow `SECURITY.md` instead of opening a public exploit report.
