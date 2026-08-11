"""Tabular OHLCV normalization helpers.

The adapters in this module convert common record- and CSV-shaped inputs into the
canonical :class:`OHLCVRow` representation without requiring pandas.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Any

from .validation import OHLCVRow, ValidationIssue, validate_ohlcv

_CANONICAL_FIELDS = ("date", "open", "high", "low", "close", "volume")
_DEFAULT_ALIASES: dict[str, tuple[str, ...]] = {
    "date": (
        "date",
        "datetime",
        "timestamp",
        "time",
        "trading_date",
        "日期",
        "交易日期",
    ),
    "open": ("open", "o", "open_price", "開盤", "開盤價"),
    "high": ("high", "h", "high_price", "最高", "最高價"),
    "low": ("low", "l", "low_price", "最低", "最低價"),
    "close": (
        "close",
        "c",
        "close_price",
        "adj_close",
        "adjusted_close",
        "收盤",
        "收盤價",
    ),
    "volume": (
        "volume",
        "vol",
        "v",
        "trade_volume",
        "成交量",
        "成交股數",
    ),
}


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Normalized rows plus validation issues for the resulting series."""

    rows: list[OHLCVRow]
    issues: list[ValidationIssue]


def _normalized_key(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def infer_column_map(columns: Iterable[Any]) -> dict[str, str]:
    """Infer canonical OHLCV fields from common English or Traditional Chinese names.

    Returns a mapping from canonical field name to the original source column.
    Raises ``ValueError`` when any required field cannot be resolved.
    """
    original_by_normalized: dict[str, str] = {}
    for column in columns:
        original = str(column)
        original_by_normalized.setdefault(_normalized_key(column), original)

    resolved: dict[str, str] = {}
    missing: list[str] = []
    for canonical in _CANONICAL_FIELDS:
        match = next(
            (
                original_by_normalized[alias]
                for alias in _DEFAULT_ALIASES[canonical]
                if alias in original_by_normalized
            ),
            None,
        )
        if match is None:
            missing.append(canonical)
        else:
            resolved[canonical] = match

    if missing:
        raise ValueError(f"Could not resolve required OHLCV columns: {', '.join(missing)}")
    return resolved


def _parse_roc_date(raw: str) -> date | None:
    """Parse common ROC-calendar date strings such as ``115/08/11`` or ``1150811``."""
    match = re.fullmatch(r"(\d{3})[/-]?(\d{2})[/-]?(\d{2})", raw)
    if match is None:
        return None

    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year + 1911, month, day)
    except ValueError as exc:
        raise ValueError(f"invalid ROC date value: {raw!r}") from exc


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    raw = str(value).strip()
    if not raw:
        raise ValueError("date is empty")

    roc_date = _parse_roc_date(raw)
    if roc_date is not None:
        return roc_date

    candidates = ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d")
    for fmt in candidates:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise ValueError(f"unsupported date value: {value!r}") from exc


def _parse_decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    raw = str(value).strip().replace(",", "")
    if not raw:
        raise ValueError(f"{field} is empty")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid {field} value: {value!r}") from exc


def _parse_volume(value: Any) -> int:
    raw = str(value).strip().replace(",", "")
    if not raw:
        raise ValueError("volume is empty")
    try:
        decimal_value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid volume value: {value!r}") from exc
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"volume must be an integer: {value!r}")
    return int(decimal_value)


def normalize_ohlcv_records(
    records: Iterable[Mapping[str, Any]],
    *,
    column_map: Mapping[str, str] | None = None,
    sort: bool = True,
) -> list[OHLCVRow]:
    """Normalize mapping-like rows into canonical ``OHLCVRow`` objects.

    ``column_map`` maps canonical names (``date/open/high/low/close/volume``) to
    source column names. When omitted, common aliases are inferred from the first
    record. Gregorian and common ROC-calendar dates are accepted.
    """
    materialized = list(records)
    if not materialized:
        return []

    if column_map is None:
        resolved = infer_column_map(materialized[0].keys())
    else:
        unknown = set(column_map) - set(_CANONICAL_FIELDS)
        if unknown:
            raise ValueError(f"Unknown canonical fields: {', '.join(sorted(unknown))}")
        missing = set(_CANONICAL_FIELDS) - set(column_map)
        if missing:
            raise ValueError(f"Missing canonical fields: {', '.join(sorted(missing))}")
        resolved = dict(column_map)

    rows: list[OHLCVRow] = []
    for index, record in enumerate(materialized, start=1):
        try:
            values = {canonical: record[source] for canonical, source in resolved.items()}
        except KeyError as exc:
            raise ValueError(
                f"Row {index} is missing source column {exc.args[0]!r}"
            ) from exc

        try:
            row = OHLCVRow(
                date=_parse_date(values["date"]),
                open=_parse_decimal(values["open"], field="open"),
                high=_parse_decimal(values["high"], field="high"),
                low=_parse_decimal(values["low"], field="low"),
                close=_parse_decimal(values["close"], field="close"),
                volume=_parse_volume(values["volume"]),
            )
        except ValueError as exc:
            raise ValueError(f"Row {index}: {exc}") from exc
        rows.append(row)

    if sort:
        rows.sort(key=lambda item: item.date)
    return rows


def normalize_and_validate_ohlcv_records(
    records: Iterable[Mapping[str, Any]],
    *,
    column_map: Mapping[str, str] | None = None,
    sort: bool = True,
) -> NormalizationResult:
    """Normalize records and immediately run the toolkit's OHLCV validator."""
    rows = normalize_ohlcv_records(records, column_map=column_map, sort=sort)
    return NormalizationResult(rows=rows, issues=validate_ohlcv(rows))


def parse_ohlcv_csv(
    text: str,
    *,
    column_map: Mapping[str, str] | None = None,
    sort: bool = True,
) -> list[OHLCVRow]:
    """Normalize OHLCV rows from CSV text."""
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV input must include a header row")
    return normalize_ohlcv_records(reader, column_map=column_map, sort=sort)


def read_ohlcv_csv(
    path: str | Path,
    *,
    column_map: Mapping[str, str] | None = None,
    sort: bool = True,
    encoding: str = "utf-8-sig",
) -> list[OHLCVRow]:
    """Read and normalize an OHLCV CSV file from disk."""
    content = Path(path).read_text(encoding=encoding)
    return parse_ohlcv_csv(content, column_map=column_map, sort=sort)


def dataframe_to_ohlcv(
    frame: Any,
    *,
    column_map: Mapping[str, str] | None = None,
    sort: bool = True,
) -> list[OHLCVRow]:
    """Normalize a pandas-like DataFrame without making pandas a dependency.

    The object only needs to provide ``to_dict(orient="records")``.
    """
    to_dict = getattr(frame, "to_dict", None)
    if not callable(to_dict):
        raise TypeError("frame must provide to_dict(orient='records')")
    records = to_dict(orient="records")
    if not isinstance(records, list):
        raise TypeError("frame.to_dict(orient='records') must return a list")
    return normalize_ohlcv_records(records, column_map=column_map, sort=sort)
