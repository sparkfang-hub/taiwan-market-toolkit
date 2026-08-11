# Reproducible local snapshots

Official exchange OpenAPI endpoints generally expose a current snapshot. If a research pipeline needs to reproduce what it saw on a particular day, it should preserve the exact response body it consumed rather than relying on a later request to return the same content.

Taiwan Market Toolkit provides a small filesystem archive for this purpose.

## Archive from the CLI

Store the current official TWSE closing snapshot:

```bash
tw-market archive-quotes --market TWSE --root market-data
```

Store the current official TPEx main-board closing snapshot:

```bash
tw-market archive-quotes --market TPEX --root market-data
```

Files are stored deterministically by source and trading date:

```text
market-data/
  twse/
    closing_quotes/
      2026/
        2026-08-11.json
  tpex/
    closing_quotes/
      2026/
        2026-08-11.json
```

The CLI returns JSON containing the source, trading date, local path, SHA-256 digest, byte count, and whether the file was created or explicitly replaced.

## Python API

```python
from taiwan_market_toolkit import archive_official_closing_snapshot

result = archive_official_closing_snapshot(
    "TWSE",
    "market-data",
)
print(result.path)
print(result.sha256)
```

For arbitrary cached JSON payloads, use `SnapshotStore` directly:

```python
from datetime import date
from taiwan_market_toolkit import SnapshotStore

store = SnapshotStore("market-data")
store.put(
    "my_source/example",
    date(2026, 8, 11),
    raw_json_bytes,
)
```

## Integrity behavior

The archive is intentionally conservative.

- Exact response bytes are preserved; the writer does not reformat or normalize JSON before storing it.
- Identical repeated writes are idempotent.
- If different bytes are already stored for the same source/date, the write fails instead of silently changing historical evidence.
- A caller may explicitly opt into replacement with `replace=True` or `--replace`.
- Every write result includes a SHA-256 digest.
- Source names are validated before they become filesystem paths; path traversal components are rejected.
- The store accepts only non-empty valid UTF-8 JSON payloads.

## What this archive is not

`SnapshotStore` is not a database, scheduler, remote backup service, or market-data redistribution service. It writes only to a caller-selected local filesystem path. The repository does not commit downloaded exchange snapshots by default.

A production collector can schedule `archive-quotes` externally and then transform archived raw responses into its own derived datasets. Keeping raw capture separate from derived analytics makes it easier to audit transformations and reproduce old calculations.
