"""TWSE holiday-schedule provider.

The Taiwan Stock Exchange publishes an official OpenAPI endpoint for the
currently published market open/closure schedule:
https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule

This module keeps network access optional and separates parsing from fetching so
applications can cache responses and tests can use fixtures.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.request import Request, urlopen

from .calendar import TaiwanTradingCalendar

TWSE_HOLIDAY_SCHEDULE_URL = (
    "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
)

_OPEN_MARKERS = ("開始交易", "最後交易", "補行交易")


@dataclass(frozen=True, slots=True)
class TWSEHolidayRecord:
    """One row from the official TWSE holiday schedule."""

    name: str
    day: date
    weekday: str
    description: str

    @property
    def market_open(self) -> bool:
        """Return whether the row explicitly describes an open trading day."""
        return any(marker in self.name for marker in _OPEN_MARKERS)

    @property
    def market_closed(self) -> bool:
        """Return whether the row describes a market closure."""
        return not self.market_open


def parse_roc_date(value: str) -> date:
    """Parse TWSE ROC dates such as ``1150101`` into Gregorian dates."""
    raw = value.strip()
    if len(raw) < 6 or not raw.isdigit():
        raise ValueError(f"Invalid TWSE ROC date: {value!r}")

    roc_year = int(raw[:-4])
    month = int(raw[-4:-2])
    day = int(raw[-2:])
    if roc_year <= 0:
        raise ValueError(f"Invalid TWSE ROC year: {value!r}")
    return date(roc_year + 1911, month, day)


def parse_twse_holiday_payload(payload: str | bytes) -> list[TWSEHolidayRecord]:
    """Parse the JSON payload returned by the TWSE holiday OpenAPI."""
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")

    parsed: Any = json.loads(payload)
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes, bytearray)):
        raise ValueError("TWSE holiday payload must be a JSON array")

    records: list[TWSEHolidayRecord] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, Mapping):
            raise ValueError(f"TWSE holiday row {index} must be an object")

        try:
            name = str(item["Name"]).strip()
            raw_date = str(item["Date"]).strip()
        except KeyError as exc:
            raise ValueError(f"TWSE holiday row {index} is missing {exc.args[0]!r}") from exc

        records.append(
            TWSEHolidayRecord(
                name=name,
                day=parse_roc_date(raw_date),
                weekday=str(item.get("Weekday", "")).strip(),
                description=str(item.get("Description", "")).strip(),
            )
        )

    return records


def fetch_twse_holiday_schedule(*, timeout: float = 10.0) -> list[TWSEHolidayRecord]:
    """Fetch and parse the official TWSE holiday schedule."""
    request = Request(
        TWSE_HOLIDAY_SCHEDULE_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "taiwan-market-toolkit/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = response.read()
    return parse_twse_holiday_payload(payload)


def calendar_from_twse_records(
    records: Iterable[TWSEHolidayRecord],
) -> TaiwanTradingCalendar:
    """Build a trading calendar from TWSE schedule records."""
    closures: set[date] = set()
    openings: set[date] = set()

    for record in records:
        if record.market_open:
            openings.add(record.day)
        else:
            closures.add(record.day)

    return TaiwanTradingCalendar.from_overrides(
        closures=closures,
        openings=openings,
    )


def fetch_twse_calendar(*, timeout: float = 10.0) -> TaiwanTradingCalendar:
    """Fetch the official schedule and return a ready-to-query calendar."""
    return calendar_from_twse_records(fetch_twse_holiday_schedule(timeout=timeout))
