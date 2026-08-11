"""Official TWSE/TPEx ex-rights and ex-dividend announcement adapters.

Both exchanges publish machine-readable ex-rights/ex-dividend preview tables, but
use different field names. This module normalizes the common announcement fields
needed by research pipelines while preserving missing or not-yet-announced values
as ``None``.

The model is announcement data, not an adjusted-price engine. It intentionally
keeps corporate-action inputs separate from any later price-adjustment method so
methodology can remain explicit and reproducible.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from .symbols import Market, normalize_market, normalize_symbol
from .twse import parse_roc_date

TWSE_CORPORATE_ACTIONS_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
TPEX_CORPORATE_ACTIONS_URL = "https://www.tpex.org.tw/openapi/v1/tpex_exright_prepost"


class CorporateActionKind(str, Enum):
    """Normalized ex-rights/ex-dividend event type."""

    EX_RIGHTS = "ex-rights"
    EX_DIVIDEND = "ex-dividend"
    EX_RIGHTS_DIVIDEND = "ex-rights-dividend"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class CorporateAction:
    """One official ex-rights/ex-dividend announcement row."""

    market: Market
    date: date
    code: str
    name: str
    kind: CorporateActionKind
    raw_action: str
    stock_dividend_ratio: Decimal | None
    subscription_ratio: Decimal | None
    subscription_price_per_share: Decimal | None
    cash_dividend_per_share: Decimal | None
    public_underwriting_shares: int | None
    employee_subscription_shares: int | None
    existing_shareholder_subscription_shares: int | None
    existing_shareholder_subscription_per_thousand: Decimal | None
    source: str

    @property
    def yahoo(self) -> str:
        """Return the common Yahoo-style market suffix for this security."""
        suffix = "TW" if self.market is Market.TWSE else "TWO"
        return f"{self.code}.{suffix}"


_MISSING_TEXT = {
    "",
    "-",
    "--",
    "---",
    "－",
    "N/A",
    "NA",
    "null",
    "None",
    "尚未公告",
    "待公告",
    "待公告實際收益分配金額",
}


def _json_rows(payload: str | bytes, *, source: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")
    parsed: Any = json.loads(payload)
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes, bytearray)):
        raise ValueError(f"{source} corporate-action payload must be a JSON array")

    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, Mapping):
            raise ValueError(f"{source} corporate-action row {index} must be an object")
        rows.append(item)
    return rows


def _clean_text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _optional_decimal(value: Any) -> Decimal | None:
    raw = _clean_text(value).replace(",", "").replace("%", "")
    if raw in _MISSING_TEXT:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid corporate-action numeric value: {value!r}") from exc


def _optional_int(value: Any) -> int | None:
    number = _optional_decimal(value)
    if number is None:
        return None
    if number != number.to_integral_value():
        raise ValueError(f"expected integral share count, got {value!r}")
    return int(number)


def _kind(value: Any) -> tuple[CorporateActionKind, str]:
    raw = _clean_text(value)
    compact = raw.replace("除", "")
    if compact == "權":
        return CorporateActionKind.EX_RIGHTS, raw
    if compact == "息":
        return CorporateActionKind.EX_DIVIDEND, raw
    if compact in {"權息", "息權"}:
        return CorporateActionKind.EX_RIGHTS_DIVIDEND, raw
    return CorporateActionKind.OTHER, raw


def _required_text(row: Mapping[str, Any], key: str, *, source: str, index: int) -> str:
    if key not in row:
        raise ValueError(f"{source} corporate-action row {index} is missing {key!r}")
    value = _clean_text(row[key])
    if not value:
        raise ValueError(f"{source} corporate-action row {index} has empty {key!r}")
    return value


def parse_twse_corporate_actions(payload: str | bytes) -> list[CorporateAction]:
    """Parse TWSE ``exchangeReport/TWT48U_ALL`` announcement rows."""
    result: list[CorporateAction] = []
    for index, row in enumerate(_json_rows(payload, source="TWSE")):
        raw_action = _required_text(row, "Exdividend", source="TWSE", index=index)
        kind, raw_action = _kind(raw_action)
        result.append(
            CorporateAction(
                market=Market.TWSE,
                date=parse_roc_date(_required_text(row, "Date", source="TWSE", index=index)),
                code=_required_text(row, "Code", source="TWSE", index=index),
                name=_required_text(row, "Name", source="TWSE", index=index),
                kind=kind,
                raw_action=raw_action,
                stock_dividend_ratio=_optional_decimal(row.get("StockDividendRatio")),
                subscription_ratio=_optional_decimal(row.get("SubscriptionRatio")),
                subscription_price_per_share=_optional_decimal(
                    row.get("SubscriptionPricePerShare")
                ),
                cash_dividend_per_share=_optional_decimal(row.get("CashDividend")),
                public_underwriting_shares=_optional_int(row.get("SharesOffered")),
                employee_subscription_shares=_optional_int(row.get("SharesEmpOwner")),
                existing_shareholder_subscription_shares=_optional_int(
                    row.get("SharesholderOwner")
                ),
                existing_shareholder_subscription_per_thousand=_optional_decimal(
                    row.get("StockHoldingRatio")
                ),
                source="TWSE exchangeReport/TWT48U_ALL",
            )
        )
    return result


def parse_tpex_corporate_actions(payload: str | bytes) -> list[CorporateAction]:
    """Parse TPEx ``tpex_exright_prepost`` announcement rows."""
    result: list[CorporateAction] = []
    for index, row in enumerate(_json_rows(payload, source="TPEx")):
        raw_action = _required_text(
            row,
            "ExRrightsExDividend",
            source="TPEx",
            index=index,
        )
        kind, raw_action = _kind(raw_action)
        result.append(
            CorporateAction(
                market=Market.TPEx,
                date=parse_roc_date(
                    _required_text(
                        row,
                        "ExRrightsExDividendDate",
                        source="TPEx",
                        index=index,
                    )
                ),
                code=_required_text(
                    row,
                    "SecuritiesCompanyCode",
                    source="TPEx",
                    index=index,
                ),
                name=_required_text(row, "CompanyName", source="TPEx", index=index),
                kind=kind,
                raw_action=raw_action,
                stock_dividend_ratio=_optional_decimal(row.get("StockDividendRatio")),
                subscription_ratio=_optional_decimal(
                    row.get("SubscriptionRatioToNewSharesIssued")
                ),
                subscription_price_per_share=_optional_decimal(
                    row.get("SubscriptionPricePerShare")
                ),
                cash_dividend_per_share=_optional_decimal(row.get("CashDividend")),
                public_underwriting_shares=_optional_int(
                    row.get("AllocatedForPublicUnderwriting")
                ),
                employee_subscription_shares=_optional_int(row.get("SubscribedByEmployees")),
                existing_shareholder_subscription_shares=_optional_int(
                    row.get("SubscribedByExistingShareholders")
                ),
                existing_shareholder_subscription_per_thousand=_optional_decimal(
                    row.get("SubscribedProRataInThousandShares")
                ),
                source="TPEx tpex_exright_prepost",
            )
        )
    return result


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


def fetch_twse_corporate_actions(*, timeout: float = 10.0) -> list[CorporateAction]:
    """Fetch the current official TWSE ex-rights/ex-dividend preview table."""
    return parse_twse_corporate_actions(_fetch_payload(TWSE_CORPORATE_ACTIONS_URL, timeout=timeout))


def fetch_tpex_corporate_actions(*, timeout: float = 10.0) -> list[CorporateAction]:
    """Fetch the current official TPEx ex-rights/ex-dividend preview table."""
    return parse_tpex_corporate_actions(_fetch_payload(TPEX_CORPORATE_ACTIONS_URL, timeout=timeout))


def fetch_corporate_actions(
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> list[CorporateAction]:
    """Fetch current corporate-action announcements for one market or both."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if market is None:
        rows = [
            *fetch_twse_corporate_actions(timeout=timeout),
            *fetch_tpex_corporate_actions(timeout=timeout),
        ]
    else:
        resolved = normalize_market(market)
        rows = (
            fetch_twse_corporate_actions(timeout=timeout)
            if resolved is Market.TWSE
            else fetch_tpex_corporate_actions(timeout=timeout)
        )
    return sorted(rows, key=lambda row: (row.date, row.market.value, row.code))


def filter_corporate_actions(
    rows: Sequence[CorporateAction],
    *,
    code: str | None = None,
    market: Market | str | None = None,
    start: date | None = None,
    end: date | None = None,
    kind: CorporateActionKind | str | None = None,
) -> list[CorporateAction]:
    """Filter already-fetched announcements without network access."""
    if start is not None and end is not None and end < start:
        raise ValueError("end must be on or after start")
    resolved_market = normalize_market(market) if market is not None else None
    resolved_kind = CorporateActionKind(kind) if kind is not None else None
    normalized_code = code.strip() if code is not None else None
    if normalized_code == "":
        raise ValueError("code must not be empty")

    result = []
    for row in rows:
        if normalized_code is not None and row.code != normalized_code:
            continue
        if resolved_market is not None and row.market is not resolved_market:
            continue
        if start is not None and row.date < start:
            continue
        if end is not None and row.date > end:
            continue
        if resolved_kind is not None and row.kind is not resolved_kind:
            continue
        result.append(row)
    return sorted(result, key=lambda row: (row.date, row.market.value, row.code))


def find_corporate_actions(
    value: str,
    market: Market | str | None = None,
    *,
    start: date | None = None,
    end: date | None = None,
    timeout: float = 10.0,
) -> list[CorporateAction]:
    """Fetch current announcements for one security without guessing its market."""
    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare Taiwan ticker")
    rows = fetch_corporate_actions(symbol.market, timeout=timeout)
    return filter_corporate_actions(
        rows,
        code=symbol.code,
        market=symbol.market,
        start=start,
        end=end,
    )


def write_corporate_actions_csv(
    rows: Iterable[CorporateAction],
    path: str | Path,
) -> Path:
    """Write normalized corporate-action announcements to UTF-8 CSV."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "date",
                "market",
                "code",
                "yahoo",
                "name",
                "kind",
                "raw_action",
                "stock_dividend_ratio",
                "subscription_ratio",
                "subscription_price_per_share",
                "cash_dividend_per_share",
                "public_underwriting_shares",
                "employee_subscription_shares",
                "existing_shareholder_subscription_shares",
                "existing_shareholder_subscription_per_thousand",
                "source",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.date.isoformat(),
                    row.market.value,
                    row.code,
                    row.yahoo,
                    row.name,
                    row.kind.value,
                    row.raw_action,
                    row.stock_dividend_ratio,
                    row.subscription_ratio,
                    row.subscription_price_per_share,
                    row.cash_dividend_per_share,
                    row.public_underwriting_shares,
                    row.employee_subscription_shares,
                    row.existing_shareholder_subscription_shares,
                    row.existing_shareholder_subscription_per_thousand,
                    row.source,
                ]
            )
    return destination
