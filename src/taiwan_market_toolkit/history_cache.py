"""Local exact-byte cache for official monthly historical responses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .symbols import Market, normalize_market


@dataclass(frozen=True, slots=True)
class HistoryCacheWriteResult:
    """Result metadata for one cache write."""

    path: Path
    sha256: str
    bytes: int
    created: bool
    replaced: bool


class HistoricalPayloadCache:
    """Filesystem cache for exact official monthly JSON response bytes.

    Layout::

        <root>/<market>/<code>/<year>/<YYYY-MM>.json
        <root>/<market>/<code>/<year>/<YYYY-MM>.json.sha256

    The cache is intentionally dumb storage: parsing and interpretation remain
    in the exchange adapters. This makes cached payloads reproducible and easy
    to inspect without coupling the toolkit to a database.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @staticmethod
    def _validate_code(code: str) -> str:
        value = code.strip().upper()
        if not value or not value.isalnum():
            raise ValueError(f"unsafe security code for cache path: {code!r}")
        return value

    @staticmethod
    def _month_start(month: date) -> date:
        return date(month.year, month.month, 1)

    def path_for(self, market: Market | str, code: str, month: date) -> Path:
        """Return the deterministic path for one market/security/month."""
        resolved_market = normalize_market(market)
        safe_code = self._validate_code(code)
        month_start = self._month_start(month)
        return (
            self.root
            / resolved_market.value.lower()
            / safe_code
            / f"{month_start.year:04d}"
            / f"{month_start:%Y-%m}.json"
        )

    def digest_path_for(self, market: Market | str, code: str, month: date) -> Path:
        """Return the sidecar SHA-256 path for one cached payload."""
        path = self.path_for(market, code, month)
        return path.with_name(f"{path.name}.sha256")

    def read(self, market: Market | str, code: str, month: date) -> bytes | None:
        """Read cached bytes, verifying the digest sidecar when present."""
        path = self.path_for(market, code, month)
        if not path.exists():
            return None

        payload = path.read_bytes()
        digest_path = self.digest_path_for(market, code, month)
        if digest_path.exists():
            expected = digest_path.read_text(encoding="ascii").strip().lower()
            actual = hashlib.sha256(payload).hexdigest()
            if expected != actual:
                raise ValueError(f"cached historical payload failed SHA-256 verification: {path}")
        return payload

    def write(
        self,
        market: Market | str,
        code: str,
        month: date,
        payload: bytes,
        *,
        replace: bool = False,
    ) -> HistoryCacheWriteResult:
        """Persist exact JSON bytes without silently replacing changed history."""
        try:
            decoded = payload.decode("utf-8-sig")
            parsed = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("historical cache payload must be valid UTF-8 JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("historical cache payload must contain a JSON object")

        path = self.path_for(market, code, month)
        digest_path = self.digest_path_for(market, code, month)
        digest = hashlib.sha256(payload).hexdigest()
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            previous = path.read_bytes()
            if previous == payload:
                digest_path.write_text(f"{digest}\n", encoding="ascii")
                return HistoryCacheWriteResult(
                    path=path,
                    sha256=digest,
                    bytes=len(payload),
                    created=False,
                    replaced=False,
                )
            if not replace:
                raise FileExistsError(
                    f"different historical payload already cached for "
                    f"{normalize_market(market).value} {code} {month:%Y-%m}"
                )

        existed = path.exists()
        path.write_bytes(payload)
        digest_path.write_text(f"{digest}\n", encoding="ascii")
        return HistoryCacheWriteResult(
            path=path,
            sha256=digest,
            bytes=len(payload),
            created=not existed,
            replaced=existed,
        )
