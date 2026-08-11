"""Official historical daily-price adapters for Taiwan common equities.

The TWSE and TPEx public historical pages expose one month per request.  This
module keeps network fetching separate from parsing, normalizes both sources
into one read-only model, and applies conservative pacing/retry behavior.

The first version intentionally targets ordinary four-digit common-equity
symbols.  Exchange-traded products can use different trading-unit conventions
and should not be silently coerced into share-volume semantics.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from .symbols import Market, normalize_symbol
from .validation import OHLCVRow

TWSE_HISTORY_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
TPEX_HISTORY_URL = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"


class HistoricalPriceError(RuntimeError):
    """Raised when an official historical-price response cannot be used safely."""


@dataclass(frozen=True, slots=True)
class HistoricalPrice:
    """One official daily observation for a Taiwan common equity."""

    market: Market
    code: str
    date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: int
    trade_value: int | None
    change: Decimal | None
    transactions: int | None
    source: str

    @property
    def has_ohlc(self) -> bool:
        """Whether all four OHLC values are present."""
        return None not in (self.open, self.high, self.low, self.close)

    def to_ohlcv(self) -> OHLCVRow:
        """Convert a fully-priced observation to the toolkit OHLCV model."""
        if not self.has_ohlc:
            raise ValueError(f"{self.code} {self.date.isoformat()} has incomplete OHLC data")
        assert self.open is not None
        assert self.high is not None
        assert self.low is not None
        assert self.close is not None
        return OHLCVRow(
            date=self.date,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )


def _parse_roc_date(value: Any) -> date:
    raw = str(value).strip()
    parts = raw.replace("-", "/").split("/")
    if len(parts) != 3:
        raise ValueError(f"unsupported ROC date: {value!r}")
    year, month, day = (int(part) for part in parts)
    if year < 1911:
        year += 1911
    return date(year, month, day)


def _clean_numeric(value: Any) -> str | None:
    raw = str(value).strip().replace(",", "").replace(" ", "")
    if not raw or raw in {"--", "---", "-", "N/A", "null", "None"}:
        return None
    while raw and raw[0] in {"+", "X", "x"}:
        raw = raw[1:]
    return raw or None


def _parse_decimal(value: Any) -> Decimal | None:
    raw = _clean_numeric(value)
    if raw is None:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal value: {value!r}") from exc


def _parse_int(value: Any) -> int | None:
    raw = _clean_numeric(value)
    if raw is None:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid integer value: {value!r}") from exc
    if number != number.to_integral_value():
        raise ValueError(f"expected integer value: {value!r}")
    return int(number)


def _is_no_data_message(value: Any) -> bool:
    text = str(value or "").lower()
    return any(token in text for token in ("沒有", "查無", "no data", "not found"))


def _ensure_equity_code(code: str) -> None:
    if len(code) != 4 or not code.isdigit():
        raise ValueError(
            "Historical price v0.1 supports ordinary four-digit Taiwan common-equity codes "
            "only; non-equity products can use different trading-unit conventions."
        )


def parse_twse_history(payload: str | bytes, code: str) -> list[HistoricalPrice]:
    """Parse one TWSE monthly STOCK_DAY JSON response."""
    _ensure_equity_code(code)
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HistoricalPriceError("TWSE historical response was not valid JSON") from exc
    if not isinstance(data, dict):
        raise HistoricalPriceError("Unexpected TWSE historical payload shape")

    stat = data.get("stat")
    rows = data.get("data")
    if not isinstance(rows, list):
        if _is_no_data_message(stat):
            return []
        raise HistoricalPriceError(f"Unexpected TWSE historical status: {stat!r}")

    out: list[HistoricalPrice] = []
    invalid = 0
    for row in rows:
        if not isinstance(row, list) or len(row) < 9:
            invalid += 1
            continue
        try:
            volume = _parse_int(row[1])
            out.append(
                HistoricalPrice(
                    market=Market.TWSE,
                    code=code,
                    date=_parse_roc_date(row[0]),
                    volume=volume or 0,
                    trade_value=_parse_int(row[2]),
                    open=_parse_decimal(row[3]),
                    high=_parse_decimal(row[4]),
                    low=_parse_decimal(row[5]),
                    close=_parse_decimal(row[6]),
                    change=_parse_decimal(row[7]),
                    transactions=_parse_int(row[8]),
                    source="TWSE exchangeReport/STOCK_DAY",
                )
            )
        except (TypeError, ValueError):
            invalid += 1

    if rows and not out and invalid:
        raise HistoricalPriceError("All TWSE historical rows were unparsable; schema may have changed")
    return out


def parse_tpex_history(payload: str | bytes, code: str) -> list[HistoricalPrice]:
    """Parse one TPEx monthly tradingStock JSON response.

    TPEx labels common-stock quantities as trading lots and trade value in
    thousands of TWD.  For the four-digit common-equity scope of this adapter,
    those are normalized to shares and TWD by multiplying each by 1,000.
    """
    _ensure_equity_code(code)
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HistoricalPriceError("TPEx historical response was not valid JSON") from exc
    if not isinstance(data, dict):
        raise HistoricalPriceError("Unexpected TPEx historical payload shape")

    stat = data.get("stat")
    tables = data.get("tables")
    if not isinstance(tables, list) or not tables:
        if _is_no_data_message(stat):
            return []
        raise HistoricalPriceError(f"Unexpected TPEx historical status: {stat!r}")

    table = tables[0]
    if not isinstance(table, dict) or not isinstance(table.get("data"), list):
        if _is_no_data_message(stat):
            return []
        raise HistoricalPriceError("Unexpected TPEx historical table shape")

    rows = table["data"]
    out: list[HistoricalPrice] = []
    invalid = 0
    for row in rows:
        if not isinstance(row, list) or len(row) < 9:
            invalid += 1
            continue
        try:
            lots = _parse_int(row[1])
            trade_value_thousands = _parse_int(row[2])
            out.append(
                HistoricalPrice(
                    market=Market.TPEx,
                    code=code,
                    date=_parse_roc_date(row[0]),
                    volume=(lots or 0) * 1000,
                    trade_value=(
                        trade_value_thousands * 1000
                        if trade_value_thousands is not None
                        else None
                    ),
                    open=_parse_decimal(row[3]),
                    high=_parse_decimal(row[4]),
                    low=_parse_decimal(row[5]),
                    close=_parse_decimal(row[6]),
                    change=_parse_decimal(row[7]),
                    transactions=_parse_int(row[8]),
                    source="TPEx afterTrading/tradingStock",
                )
            )
        except (TypeError, ValueError):
            invalid += 1

    if rows and not out and invalid:
        raise HistoricalPriceError("All TPEx historical rows were unparsable; schema may have changed")
    return out


def _month_starts(start: date, end: date) -> Iterator[date]:
    current = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while current <= last:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def _fetch_text(url: str, *, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "taiwan-market-toolkit/0.1 (+https://github.com/sparkfang-hub/taiwan-market-toolkit)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


def fetch_twse_history_month(code: str, month: date, *, timeout: float = 10.0) -> list[HistoricalPrice]:
    """Fetch one calendar month of official TWSE daily prices."""
    _ensure_equity_code(code)
    query = urllib.parse.urlencode(
        {
            "response": "json",
            "date": month.strftime("%Y%m01"),
            "stockNo": code,
        }
    )
    return parse_twse_history(_fetch_text(f"{TWSE_HISTORY_URL}?{query}", timeout=timeout), code)


def fetch_tpex_history_month(code: str, month: date, *, timeout: float = 10.0) -> list[HistoricalPrice]:
    """Fetch one calendar month of official TPEx daily prices."""
    _ensure_equity_code(code)
    query = urllib.parse.urlencode(
        {
            "date": month.strftime("%Y/%m/01"),
            "code": code,
            "response": "json",
        }
    )
    return parse_tpex_history(_fetch_text(f"{TPEX_HISTORY_URL}?{query}", timeout=timeout), code)


def fetch_price_history(
    value: str,
    market: Market | str | None = None,
    *,
    start: date,
    end: date,
    timeout: float = 10.0,
    request_interval: float = 0.25,
    max_retries: int = 2,
    retry_backoff: float = 0.75,
    max_months: int = 120,
) -> list[HistoricalPrice]:
    """Fetch a date range from the appropriate official exchange source.

    Requests are monthly, paced, retried only for transport/temporary JSON
    failures, and capped by ``max_months`` to avoid accidentally hammering a
    public exchange endpoint.
    """
    if end < start:
        raise ValueError("end must be on or after start")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if request_interval < 0 or retry_backoff < 0:
        raise ValueError("request timing values cannot be negative")
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    if max_months <= 0:
        raise ValueError("max_months must be positive")

    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare ticker without .TW or .TWO")
    _ensure_equity_code(symbol.code)

    months = list(_month_starts(start, end))
    if len(months) > max_months:
        raise ValueError(
            f"requested range spans {len(months)} months; max_months is {max_months}"
        )

    if symbol.market is Market.TWSE:
        fetch_month = fetch_twse_history_month
    else:
        fetch_month = fetch_tpex_history_month

    collected: list[HistoricalPrice] = []
    for index, month in enumerate(months):
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                collected.extend(fetch_month(symbol.code, month, timeout=timeout))
                last_error = None
                break
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
            except HistoricalPriceError as exc:
                # Invalid JSON can be a transient CDN response; schema errors should
                # remain visible after the small retry budget.
                last_error = exc
            if attempt < max_retries:
                time.sleep(retry_backoff * (2**attempt))
        if last_error is not None:
            raise HistoricalPriceError(
                f"failed to fetch {symbol.market.value} {symbol.code} {month:%Y-%m}"
            ) from last_error
        if index < len(months) - 1 and request_interval:
            time.sleep(request_interval)

    unique: dict[date, HistoricalPrice] = {}
    for item in collected:
        if start <= item.date <= end:
            unique[item.date] = item
    return [unique[key] for key in sorted(unique)]


def history_to_ohlcv(
    prices: Iterable[HistoricalPrice],
    *,
    strict: bool = False,
) -> list[OHLCVRow]:
    """Convert historical observations into canonical OHLCV rows.

    By default, observations with missing official OHLC values are skipped.
    ``strict=True`` raises instead, which is useful for reproducibility checks.
    """
    rows: list[OHLCVRow] = []
    for item in prices:
        if not item.has_ohlc:
            if strict:
                item.to_ohlcv()
            continue
        rows.append(item.to_ohlcv())
    return rows


def write_history_csv(prices: Iterable[HistoricalPrice], path: str | Path) -> Path:
    """Write normalized historical observations to a UTF-8 CSV file."""
    import csv

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "date",
                "market",
                "code",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trade_value",
                "change",
                "transactions",
                "source",
            ]
        )
        for item in prices:
            writer.writerow(
                [
                    item.date.isoformat(),
                    item.market.value,
                    item.code,
                    item.open,
                    item.high,
                    item.low,
                    item.close,
                    item.volume,
                    item.trade_value,
                    item.change,
                    item.transactions,
                    item.source,
                ]
            )
    return destination
