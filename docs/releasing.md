# Releasing Taiwan Market Toolkit

This project is designed to publish reproducible Python distributions through GitHub Actions and PyPI Trusted Publishing.

## Before the first release

1. Create a PyPI account and enable two-factor authentication.
2. In PyPI Trusted Publishing, register a pending publisher for:
   - PyPI project: `taiwan-market-toolkit`
   - GitHub owner: `sparkfang-hub`
   - Repository: `taiwan-market-toolkit`
   - Workflow: `publish.yml`
   - Environment: `pypi`
3. In GitHub repository settings, create an environment named `pypi` and require manual approval for deployments.
4. Confirm CI is green on `main`.
5. Confirm the package name is still available on PyPI before publishing the first release.

No long-lived PyPI API token is required when Trusted Publishing is configured correctly.

## Release checklist

1. Update `CHANGELOG.md` and confirm the version in `pyproject.toml` and `src/taiwan_market_toolkit/__init__.py` match.
2. Run locally when possible:

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
python -m pip install build twine
python -m build
python -m twine check dist/*
```

3. Merge the release-preparation pull request only after CI passes.
4. Create a GitHub release using a tag such as `v0.1.0`.
5. The `Publish to PyPI` workflow builds a fresh wheel and source distribution and publishes them through OIDC Trusted Publishing.
6. Verify the package can be installed in a clean environment:

```bash
python -m venv /tmp/tmt-check
source /tmp/tmt-check/bin/activate
python -m pip install taiwan-market-toolkit
python -c "import taiwan_market_toolkit; print(taiwan_market_toolkit.__version__)"
```

## Release policy

Early releases use semantic versioning while the API is still alpha. Breaking changes may occur before `1.0.0`, but they should be documented in the changelog and accompanied by tests.

A release should represent a coherent, tested capability rather than a commit-count milestone. Public usage, bug reports, contributor feedback, and real maintenance work are more valuable signals than frequent cosmetic releases.
