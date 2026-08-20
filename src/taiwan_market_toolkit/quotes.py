"""Read-only closing-quote adapters for official Taiwan exchange OpenAPI sources.

The module exposes a deliberately small common subset shared by TWSE and TPEx:
trading date, security code, security name, market, and closing price. Network
fetching is kept separate from parsing so applications can cache raw payloads and
tests can use deterministic fixtures.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from http.client import IncompleteRead
from typing import Any
from urllib.request import Request, urlopen

from .symbols import Market, normalize_symbol

TWSE_CURRENT_QUOTES_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX_CURRENT_QUOTES_URL = (
    "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
)


@dataclass(frozen=True, slots=True)
class ClosingQuote:
    """Common closing-quote fields from an official Taiwan exchange snapshot."""

    market: Market
    date: date
    code: str
    name: str
    close: Decimal | None


def _parse_trading_date(value: Any) -> date:
    raw = str(value).strip()
    if not raw:
        raise ValueError("trading date is empty")

    iso_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if iso_match:
        year, month, day = (int(part) for part in iso_match.groups())
        return date(year, month, day)

    slash_match = re.fullmatch(r"(\d{3,4})/(\d{1,2})/(\d{1,2})", raw)
    if slash_match:
        year, month, day = (int(part) for part in slash_match.groups())
        if year < 1911:
            year += 1911
        return date(year, month, day)

    compact_match = re.fullmatch(r"(\d{3,4})(\d{2})(\d{2})", raw)
    if compact_match:
        year, month, day = (int(part) for part in compact_match.groups())
        if year < 1911:
            year += 1911
        return date(year, month, day)

    raise ValueError(f"unsupported trading date: {value!r}")


def _parse_optional_decimal(value: Any) -> Decimal | None:
    raw = str(value).strip().replace(",", "")
    if raw in {"", "-", "--", "－", "---"}:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal value: {value!r}") from exc


def _json_rows(payload: str | bytes, *, source: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")

    parsed: Any = json.loads(payload)
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes, bytearray)):
        raise ValueError(f"{source} quote payload must be a JSON array")

    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, Mapping):
            raise ValueError(f"{source} quote row {index} must be an object")
        rows.append(item)
    return rows


def parse_twse_closing_quotes(payload: str | bytes) -> list[ClosingQuote]:
    """Parse the official TWSE ``STOCK_DAY_ALL`` snapshot."""
    result: list[ClosingQuote] = []
    for index, item in enumerate(_json_rows(payload, source="TWSE")):
        required = ("Date", "Code", "Name", "ClosingPrice")
        missing = [field for field in required if field not in item]
        if missing:
            raise ValueError(f"TWSE quote row {index} is missing {', '.join(missing)}")

        result.append(
            ClosingQuote(
                market=Market.TWSE,
                date=_parse_trading_date(item["Date"]),
                code=str(item["Code"]).strip(),
                name=str(item["Name"]).strip(),
                close=_parse_optional_decimal(item["ClosingPrice"]),
            )
        )
    return result


def parse_tpex_closing_quotes(payload: str | bytes) -> list[ClosingQuote]:
    """Parse the official TPEx main-board daily close snapshot."""
    result: list[ClosingQuote] = []
    for index, item in enumerate(_json_rows(payload, source="TPEx")):
        required = ("Date", "SecuritiesCompanyCode", "CompanyName", "Close")
        missing = [field for field in required if field not in item]
        if missing:
            raise ValueError(f"TPEx quote row {index} is missing {', '.join(missing)}")

        result.append(
            ClosingQuote(
                market=Market.TPEx,
                date=_parse_trading_date(item["Date"]),
                code=str(item["SecuritiesCompanyCode"]).strip(),
                name=str(item["CompanyName"]).strip(),
                close=_parse_optional_decimal(item["Close"]),
            )
        )
    return result


def _fetch_payload(url: str, *, timeout: float) -> bytes:
    for attempt in range(2):
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "taiwan-market-toolkit/0.1",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                return response.read()
        except IncompleteRead:
            if attempt == 1:
                raise
    raise RuntimeError("unreachable")


def fetch_twse_closing_payload(*, timeout: float = 10.0) -> bytes:
    """Fetch the unmodified official TWSE closing-snapshot response body."""
    return _fetch_payload(TWSE_CURRENT_QUOTES_URL, timeout=timeout)


def fetch_tpex_closing_payload(*, timeout: float = 10.0) -> bytes:
    """Fetch the unmodified official TPEx closing-snapshot response body."""
    return _fetch_payload(TPEX_CURRENT_QUOTES_URL, timeout=timeout)


def fetch_twse_closing_quotes(*, timeout: float = 10.0) -> list[ClosingQuote]:
    """Fetch the current official TWSE all-securities closing snapshot."""
    return parse_twse_closing_quotes(fetch_twse_closing_payload(timeout=timeout))


def fetch_tpex_closing_quotes(*, timeout: float = 10.0) -> list[ClosingQuote]:
    """Fetch the current official TPEx main-board closing snapshot."""
    return parse_tpex_closing_quotes(fetch_tpex_closing_payload(timeout=timeout))


def fetch_closing_quote(
    value: str,
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> ClosingQuote:
    """Fetch one security's latest official closing quote.

    A suffix such as ``.TW``/``.TWO`` or an explicit market hint is required so
    the function never guesses which exchange should be queried.
    """
    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare Taiwan ticker")

    if symbol.market is Market.TWSE:
        quotes = fetch_twse_closing_quotes(timeout=timeout)
    else:
        quotes = fetch_tpex_closing_quotes(timeout=timeout)

    try:
        return next(quote for quote in quotes if quote.code == symbol.code)
    except StopIteration as exc:
        raise LookupError(
            f"No {symbol.market.value} closing quote found for {symbol.code}"
        ) from exc
