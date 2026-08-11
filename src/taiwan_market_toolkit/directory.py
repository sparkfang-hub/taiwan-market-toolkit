"""Unified company-directory helpers backed by official TWSE and TPEx OpenAPI data.

The public model intentionally keeps only common identity metadata needed by
market-data tools. Exchange-specific source rows remain available to callers who
need richer disclosure fields.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.request import Request, urlopen

from .symbols import Market, normalize_symbol

TWSE_COMPANY_DIRECTORY_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_COMPANY_DIRECTORY_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"


@dataclass(frozen=True, slots=True)
class SecurityProfile:
    """Common company/security identity metadata for a Taiwan-listed equity."""

    market: Market
    code: str
    name: str | None
    short_name: str | None
    english_name: str | None
    industry: str | None
    listing_date: date | None

    @property
    def yahoo(self) -> str:
        """Return a Yahoo-style ticker for the profile's known market."""
        suffix = "TW" if self.market is Market.TWSE else "TWO"
        return f"{self.code}.{suffix}"


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"[\s\u3000]+", " ", str(value)).strip()
    return None if text in {"", "-", "－", "--"} else text


def _pick(row: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _parse_optional_date(value: Any) -> date | None:
    text = _clean_text(value)
    if text is None:
        return None

    digits = re.sub(r"\D", "", text)
    if len(digits) == 8:
        first_four = int(digits[:4])
        if first_four >= 1911:
            year = first_four
            rest = digits[4:]
        else:
            year = first_four + 1911
            rest = digits[4:]
    elif len(digits) == 7:
        year = int(digits[:3]) + 1911
        rest = digits[3:]
    elif len(digits) == 6:
        year = int(digits[:2]) + 1911
        rest = digits[2:]
    else:
        raise ValueError(f"unsupported listing date: {value!r}")

    month = int(rest[:2])
    day = int(rest[2:4])
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"invalid listing date: {value!r}") from exc


def _json_rows(payload: str | bytes, *, source: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")
    parsed: Any = json.loads(payload)
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes, bytearray)):
        raise ValueError(f"{source} company-directory payload must be a JSON array")

    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, Mapping):
            raise ValueError(f"{source} company-directory row {index} must be an object")
        rows.append(item)
    return rows


def parse_twse_company_directory(payload: str | bytes) -> list[SecurityProfile]:
    """Parse official TWSE listed-company basic data into common profiles."""
    profiles: list[SecurityProfile] = []
    for index, row in enumerate(_json_rows(payload, source="TWSE")):
        code = _clean_text(_pick(row, ("公司代號", "Code", "SecuritiesCompanyCode")))
        if code is None:
            raise ValueError(f"TWSE company-directory row {index} has no company code")

        profiles.append(
            SecurityProfile(
                market=Market.TWSE,
                code=code,
                name=_clean_text(_pick(row, ("公司名稱", "CompanyName", "Name"))),
                short_name=_clean_text(
                    _pick(row, ("公司簡稱", "CompanyAbbreviation", "AbbreviatedName"))
                ),
                english_name=_clean_text(
                    _pick(row, ("英文簡稱", "英文名稱", "Symbol", "EnglishName"))
                ),
                industry=_clean_text(
                    _pick(row, ("產業別", "SecuritiesIndustryCode", "IndustryCode"))
                ),
                listing_date=_parse_optional_date(
                    _pick(row, ("上市日期", "DateOfListing", "ListingDate"))
                ),
            )
        )
    return profiles


def parse_tpex_company_directory(payload: str | bytes) -> list[SecurityProfile]:
    """Parse official TPEx main-board basic data into common profiles."""
    profiles: list[SecurityProfile] = []
    for index, row in enumerate(_json_rows(payload, source="TPEx")):
        code = _clean_text(_pick(row, ("SecuritiesCompanyCode", "公司代號", "Code")))
        if code is None:
            raise ValueError(f"TPEx company-directory row {index} has no company code")

        profiles.append(
            SecurityProfile(
                market=Market.TPEx,
                code=code,
                name=_clean_text(_pick(row, ("CompanyName", "公司名稱", "Name"))),
                short_name=_clean_text(
                    _pick(row, ("CompanyAbbreviation", "公司簡稱", "AbbreviatedName"))
                ),
                english_name=_clean_text(
                    _pick(row, ("Symbol", "英文簡稱", "英文名稱", "EnglishName"))
                ),
                industry=_clean_text(
                    _pick(row, ("SecuritiesIndustryCode", "產業別", "IndustryCode"))
                ),
                listing_date=_parse_optional_date(
                    _pick(row, ("DateOfListing", "上櫃日期", "上市日期", "ListingDate"))
                ),
            )
        )
    return profiles


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


def fetch_twse_company_directory(*, timeout: float = 10.0) -> list[SecurityProfile]:
    """Fetch the official TWSE listed-company basic-data directory."""
    payload = _fetch_payload(TWSE_COMPANY_DIRECTORY_URL, timeout=timeout)
    return parse_twse_company_directory(payload)


def fetch_tpex_company_directory(*, timeout: float = 10.0) -> list[SecurityProfile]:
    """Fetch the official TPEx main-board basic-data directory."""
    payload = _fetch_payload(TPEX_COMPANY_DIRECTORY_URL, timeout=timeout)
    return parse_tpex_company_directory(payload)


def fetch_company_directory(*, timeout: float = 10.0) -> list[SecurityProfile]:
    """Fetch and combine the official TWSE and TPEx company directories."""
    return [
        *fetch_twse_company_directory(timeout=timeout),
        *fetch_tpex_company_directory(timeout=timeout),
    ]


def find_company(
    value: str,
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> SecurityProfile:
    """Find one company by ticker without guessing the market for bare symbols."""
    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare Taiwan ticker")

    if symbol.market is Market.TWSE:
        profiles = fetch_twse_company_directory(timeout=timeout)
    else:
        profiles = fetch_tpex_company_directory(timeout=timeout)

    try:
        return next(profile for profile in profiles if profile.code == symbol.code)
    except StopIteration as exc:
        raise LookupError(
            f"No {symbol.market.value} company profile found for {symbol.code}"
        ) from exc


def search_company_directory(
    profiles: Sequence[SecurityProfile],
    query: str,
    *,
    market: Market | None = None,
    limit: int = 20,
) -> list[SecurityProfile]:
    """Search already-fetched profiles by code or company names.

    Exact code matches rank first, then code prefixes, then name/short-name/
    English-name substring matches. No network request is performed here.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    needle = query.strip().casefold()
    if not needle:
        raise ValueError("query must not be empty")

    ranked: list[tuple[int, str, SecurityProfile]] = []
    for profile in profiles:
        if market is not None and profile.market is not market:
            continue

        code = profile.code.casefold()
        names = [profile.name, profile.short_name, profile.english_name]
        folded_names = [name.casefold() for name in names if name]

        if code == needle:
            rank = 0
        elif code.startswith(needle):
            rank = 1
        elif any(name == needle for name in folded_names):
            rank = 2
        elif any(needle in name for name in folded_names):
            rank = 3
        else:
            continue
        ranked.append((rank, profile.code, profile))

    ranked.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in ranked[:limit]]
