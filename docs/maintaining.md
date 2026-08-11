# Maintainer workflow

This project sits between public exchange data sources and downstream research code. Maintenance therefore has two responsibilities: preserve a stable user-facing API where practical, and fail visibly when an upstream exchange schema or service changes.

## Pull requests

Before merging a pull request:

1. Keep network fetching separate from parsing whenever an official source is involved.
2. Add deterministic fixture tests for new parsers or transformations.
3. Preserve source dates and missing values instead of inventing synchronized or numeric values.
4. Run `ruff check .` and `pytest` locally when possible.
5. Wait for the GitHub Actions Python matrix, package build, and cross-platform wheel smoke tests to pass.
6. Update documentation and `CHANGELOG.md` when behavior visible to users changes.

Small fixes can be merged independently. Larger source integrations should use focused pull requests so failures and reversions remain easy to understand.

## Issue triage

Classify incoming reports by the layer that is failing:

- source availability: the official TWSE/TPEx service is unavailable or timing out;
- schema drift: an official response no longer matches the parser assumptions;
- normalization: the source is valid but the shared model is incorrect;
- packaging/installation: wheels, entry points, optional dependencies, or supported Python versions fail;
- documentation: expected behavior is unclear or an example is stale;
- feature request: a new source, product type, or transformation is proposed.

For source/schema reports, ask for the exchange, endpoint, observation date, and a redacted sample when legally redistributable. Never ask reporters to post brokerage credentials or private account data.

## Upstream-source incidents

Normal unit tests do not depend on live exchange uptime. Scheduled source probes are the early warning layer.

When a probe fails:

1. Confirm whether the official source itself is reachable.
2. Compare the current source shape with the parser fixture and documented provenance.
3. Do not reinterpret missing or renamed fields silently.
4. Add a regression fixture before changing parser behavior.
5. If the source is temporarily unavailable, prefer a documented incident or retry over a guessed fallback.
6. If a source is retired, deprecate the adapter explicitly and document the replacement source.

## Releases

The first public release is intentionally gated by `docs/releasing.md` and the repository release checklist issue.

For each release:

1. Confirm `main` is green.
2. Review the unreleased changelog and move shipped entries under the release version/date.
3. Verify the package version is consistent.
4. Build wheel and source distributions and run metadata validation.
5. Confirm the cross-platform wheel smoke matrix is green.
6. Publish a GitHub release only after release notes are ready.
7. Let the Trusted Publishing workflow publish to PyPI.
8. Install the published package in a clean environment and run a small offline CLI smoke test.
9. Keep any release regression visible in an issue and patch it rather than rewriting published artifacts.

## Security and data boundaries

Follow `SECURITY.md` for vulnerability reports. This project must not accept brokerage secrets, private trading strategies, private datasets without redistribution rights, or code that performs market order execution under the public package name.

## Dependency maintenance

Dependabot checks Python and GitHub Actions dependencies monthly. Dependency updates are ordinary pull requests: they must pass the same test, package, and wheel-smoke requirements as feature work. Major-version updates should include a short compatibility note when behavior could change.

## Compatibility policy during alpha

The project is currently alpha. APIs can still evolve, but changes should be deliberate and documented. Prefer additive changes. When a breaking change is necessary, explain the reason in the pull request and changelog rather than silently changing a public model.
