"""Official TWSE/TPEx valuation metrics with a small common model.

The exchanges publish P/E ratio, dividend yield, and price-to-book ratio through
separate OpenAPI schemas. This module keeps fetching separate from parsing and
preserves missing metrics as ``None`` instead of inventing numeric values.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.request import Request, urlopen

from .symbols import Market, normalize_market, normalize_symbol

TWSE_VALUATION_URL = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"
TPEX_VALUATION_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"


@dataclass(frozen=True, slots=True)
class ValuationMetrics:
    """Common daily valuation fields published by TWSE or TPEx."""

    market: Market
    date: date
    code: str
    name: str
    pe_ratio: Decimal | None
    dividend_yield_pct: Decimal | None
    price_to_book: Decimal | None
    dividend_per_share: Decimal | None = None


def _parse_date(value: Any) -> date:
    raw = str(value).strip()
    if not raw:
        raise ValueError("valuation date is empty")

    compact = re.fullmatch(r"(\d{3,4})(\d{2})(\d{2})", raw)
    separated = re.fullmatch(r"(\d{3,4})[-/](\d{1,2})[-/](\d{1,2})", raw)
    match = compact or separated
    if match is None:
        raise ValueError(f"unsupported valuation date: {value!r}")

    year, month, day = (int(part) for part in match.groups())
    if year < 1911:
        year += 1911
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"invalid valuation date: {value!r}") from exc


def _parse_optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    raw = str(value).strip().replace(",", "").replace("%", "")
    if raw in {"", "-", "--", "－", "---", "N/A", "NA"}:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid valuation value: {value!r}") from exc


def _json_rows(payload: str | bytes, *, source: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")
    parsed: Any = json.loads(payload)
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes, bytearray)):
        raise ValueError(f"{source} valuation payload must be a JSON array")

    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, Mapping):
            raise ValueError(f"{source} valuation row {index} must be an object")
        rows.append(item)
    return rows


def parse_twse_valuation(payload: str | bytes) -> list[ValuationMetrics]:
    """Parse the official TWSE ``BWIBBU_ALL`` response."""
    metrics: list[ValuationMetrics] = []
    for index, row in enumerate(_json_rows(payload, source="TWSE")):
        required = ("Date", "Code", "Name", "PEratio", "DividendYield", "PBratio")
        missing = [field for field in required if field not in row]
        if missing:
            raise ValueError(f"TWSE valuation row {index} is missing {', '.join(missing)}")

        metrics.append(
            ValuationMetrics(
                market=Market.TWSE,
                date=_parse_date(row["Date"]),
                code=str(row["Code"]).strip(),
                name=str(row["Name"]).strip(),
                pe_ratio=_parse_optional_decimal(row["PEratio"]),
                dividend_yield_pct=_parse_optional_decimal(row["DividendYield"]),
                price_to_book=_parse_optional_decimal(row["PBratio"]),
            )
        )
    return metrics


def parse_tpex_valuation(payload: str | bytes) -> list[ValuationMetrics]:
    """Parse the official TPEx ``tpex_mainboard_peratio_analysis`` response."""
    metrics: list[ValuationMetrics] = []
    for index, row in enumerate(_json_rows(payload, source="TPEx")):
        required = (
            "Date",
            "SecuritiesCompanyCode",
            "CompanyName",
            "PriceEarningRatio",
            "YieldRatio",
            "PriceBookRatio",
        )
        missing = [field for field in required if field not in row]
        if missing:
            raise ValueError(f"TPEx valuation row {index} is missing {', '.join(missing)}")

        metrics.append(
            ValuationMetrics(
                market=Market.TPEx,
                date=_parse_date(row["Date"]),
                code=str(row["SecuritiesCompanyCode"]).strip(),
                name=str(row["CompanyName"]).strip(),
                pe_ratio=_parse_optional_decimal(row["PriceEarningRatio"]),
                dividend_yield_pct=_parse_optional_decimal(row["YieldRatio"]),
                price_to_book=_parse_optional_decimal(row["PriceBookRatio"]),
                dividend_per_share=_parse_optional_decimal(row.get("DividendPerShare")),
            )
        )
    return metrics


def _fetch_payload(url: str, *, timeout: float) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "taiwan-market-toolkit/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()


def fetch_twse_valuation(*, timeout: float = 10.0) -> list[ValuationMetrics]:
    """Fetch the current official TWSE valuation snapshot."""
    return parse_twse_valuation(_fetch_payload(TWSE_VALUATION_URL, timeout=timeout))


def fetch_tpex_valuation(*, timeout: float = 10.0) -> list[ValuationMetrics]:
    """Fetch the current official TPEx valuation snapshot."""
    return parse_tpex_valuation(_fetch_payload(TPEX_VALUATION_URL, timeout=timeout))


def fetch_valuation_metrics(
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> list[ValuationMetrics]:
    """Fetch valuation metrics for one market or both markets."""
    if market is None:
        return [
            *fetch_twse_valuation(timeout=timeout),
            *fetch_tpex_valuation(timeout=timeout),
        ]

    resolved = normalize_market(market)
    if resolved is Market.TWSE:
        return fetch_twse_valuation(timeout=timeout)
    return fetch_tpex_valuation(timeout=timeout)


def find_valuation(
    value: str,
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> ValuationMetrics:
    """Fetch one security's current official valuation metrics."""
    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare Taiwan ticker")

    rows = fetch_valuation_metrics(symbol.market, timeout=timeout)
    try:
        return next(item for item in rows if item.code == symbol.code)
    except StopIteration as exc:
        raise LookupError(
            f"No {symbol.market.value} valuation metrics found for {symbol.code}"
        ) from exc
