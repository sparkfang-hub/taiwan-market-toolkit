"""Local raw-snapshot storage for reproducible market-data collection.

The archive is intentionally filesystem-only: it preserves exact official response
bytes, never sends files elsewhere, and refuses to overwrite a changed snapshot
unless the caller explicitly opts in.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .quotes import (
    fetch_tpex_closing_payload,
    fetch_twse_closing_payload,
    parse_tpex_closing_quotes,
    parse_twse_closing_quotes,
)
from .symbols import Market

_SOURCE_PART = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True, slots=True)
class SnapshotWriteResult:
    """Metadata describing one local snapshot write."""

    source: str
    date: date
    path: Path
    sha256: str
    bytes: int
    created: bool
    replaced: bool


def _source_parts(source: str) -> tuple[str, ...]:
    normalized = source.strip().replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part)
    if not parts or any(part in {".", ".."} or not _SOURCE_PART.fullmatch(part) for part in parts):
        raise ValueError(f"unsafe snapshot source: {source!r}")
    return parts


def _payload_bytes(payload: str | bytes) -> bytes:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    if not data:
        raise ValueError("snapshot payload is empty")
    try:
        json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("snapshot payload must be valid UTF-8 JSON") from exc
    return data


class SnapshotStore:
    """Store exact JSON payloads under ``source/year/date.json`` paths."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, source: str, day: date) -> Path:
        """Return the deterministic path for a source/date pair."""
        return self.root.joinpath(*_source_parts(source), f"{day.year:04d}", f"{day.isoformat()}.json")

    def put(
        self,
        source: str,
        day: date,
        payload: str | bytes,
        *,
        replace: bool = False,
    ) -> SnapshotWriteResult:
        """Store a raw JSON snapshot without silently changing an existing date.

        Writing identical bytes is idempotent. Different bytes for the same
        source/date raise ``FileExistsError`` unless ``replace=True``.
        """
        data = _payload_bytes(payload)
        destination = self.path_for(source, day)
        digest = hashlib.sha256(data).hexdigest()
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            existing = destination.read_bytes()
            if existing == data:
                return SnapshotWriteResult(
                    source=source,
                    date=day,
                    path=destination,
                    sha256=digest,
                    bytes=len(data),
                    created=False,
                    replaced=False,
                )
            if not replace:
                raise FileExistsError(
                    f"snapshot already exists with different content: {destination}"
                )

        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(destination)

        return SnapshotWriteResult(
            source=source,
            date=day,
            path=destination,
            sha256=digest,
            bytes=len(data),
            created=not destination.exists() if False else not replace,
            replaced=replace,
        )

    def read(self, source: str, day: date) -> bytes:
        """Read an exact stored response body."""
        return self.path_for(source, day).read_bytes()

    def dates(self, source: str) -> list[date]:
        """List stored snapshot dates for a source in ascending order."""
        base = self.root.joinpath(*_source_parts(source))
        if not base.exists():
            return []

        result: list[date] = []
        for path in base.glob("[0-9][0-9][0-9][0-9]/*.json"):
            try:
                result.append(date.fromisoformat(path.stem))
            except ValueError:
                continue
        return sorted(set(result))

    def latest(self, source: str) -> tuple[date, bytes] | None:
        """Return the most recent stored snapshot date and exact bytes."""
        dates = self.dates(source)
        if not dates:
            return None
        day = dates[-1]
        return day, self.read(source, day)


def _coerce_market(market: Market | str) -> Market:
    if isinstance(market, Market):
        return market
    normalized = market.strip().upper()
    if normalized in {"TWSE", "TW"}:
        return Market.TWSE
    if normalized in {"TPEX", "TWO", "OTC"}:
        return Market.TPEx
    raise ValueError(f"unsupported market: {market!r}")


def archive_official_closing_snapshot(
    market: Market | str,
    root: str | Path,
    *,
    timeout: float = 10.0,
    replace: bool = False,
) -> SnapshotWriteResult:
    """Fetch and archive one raw official closing snapshot locally."""
    resolved_market = _coerce_market(market)

    if resolved_market is Market.TWSE:
        payload = fetch_twse_closing_payload(timeout=timeout)
        quotes = parse_twse_closing_quotes(payload)
        source = "twse/closing_quotes"
    else:
        payload = fetch_tpex_closing_payload(timeout=timeout)
        quotes = parse_tpex_closing_quotes(payload)
        source = "tpex/closing_quotes"

    if not quotes:
        raise ValueError(f"{resolved_market.value} closing snapshot returned no rows")

    snapshot_date = max(quote.date for quote in quotes)
    return SnapshotStore(root).put(source, snapshot_date, payload, replace=replace)
