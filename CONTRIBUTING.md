# Contributing

Thanks for considering a contribution to Taiwan Market Toolkit.

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
5. Update documentation when adding or changing user-facing behavior.

## Data-source policy

This project aims to provide reusable market-data tooling, not to redistribute data without permission. Contributions that integrate external sources should document the source, license or terms, update frequency, and failure behavior.

## Reporting bugs

Please include a minimal reproducible example, Python version, operating system, and the smallest sample data necessary to reproduce the issue.
