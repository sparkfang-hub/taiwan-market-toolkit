"""Unified cross-source snapshots for Taiwan listed equities.

The exchange company directory is treated as the authoritative universe for this
module. Closing quotes and valuation metrics are left-joined by market and code,
so missing daily data stays explicit instead of silently dropping a listed
company from the snapshot.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar

from .directory import (
    SecurityProfile,
    fetch_company_directory,
    fetch_tpex_company_directory,
    fetch_twse_company_directory,
)
from .quotes import ClosingQuote, fetch_tpex_closing_quotes, fetch_twse_closing_quotes
from .symbols import Market, normalize_market
from .valuation import (
    ValuationMetrics,
    fetch_tpex_valuation,
    fetch_twse_valuation,
    fetch_valuation_metrics,
)


@dataclass(frozen=True, slots=True)
class MarketSnapshotRow:
    """One listed company joined with its latest official market observations."""

    market: Market
    code: str
    name: str | None
    short_name: str | None
    english_name: str | None
    industry: str | None
    listing_date: date | None
    quote_date: date | None
    close: Decimal | None
    valuation_date: date | None
    pe_ratio: Decimal | None
    dividend_yield_pct: Decimal | None
    price_to_book: Decimal | None
    dividend_per_share: Decimal | None

    @property
    def yahoo(self) -> str:
        """Return the common Yahoo-style market suffix for this security."""
        suffix = "TW" if self.market is Market.TWSE else "TWO"
        return f"{self.code}.{suffix}"

    @property
    def has_quote(self) -> bool:
        """Whether a matching closing-quote row was present in the source snapshot."""
        return self.quote_date is not None

    @property
    def has_valuation(self) -> bool:
        """Whether a matching valuation row was present in the source snapshot."""
        return self.valuation_date is not None


@dataclass(frozen=True, slots=True)
class MarketSnapshotSummary:
    """Coverage summary for a joined market snapshot."""

    rows: int
    with_quote: int
    with_valuation: int
    missing_quote: int
    missing_valuation: int
    quote_dates: tuple[date, ...]
    valuation_dates: tuple[date, ...]


T = TypeVar("T", ClosingQuote, ValuationMetrics)


def _index_unique(rows: Iterable[T], *, label: str) -> dict[tuple[Market, str], T]:
    indexed: dict[tuple[Market, str], T] = {}
    for row in rows:
        key = (row.market, row.code)
        if key in indexed:
            raise ValueError(f"duplicate {label} row for {row.market.value} {row.code}")
        indexed[key] = row
    return indexed


def build_market_snapshot(
    profiles: Sequence[SecurityProfile],
    quotes: Sequence[ClosingQuote],
    valuations: Sequence[ValuationMetrics],
    *,
    market: Market | str | None = None,
) -> list[MarketSnapshotRow]:
    """Left-join official company, closing-quote, and valuation snapshots.

    The company directory defines the listed-equity universe. Quote and valuation
    feeds can contain additional security types, so they are never allowed to add
    rows on their own.
    """
    resolved_market = normalize_market(market) if market is not None else None
    quote_index = _index_unique(quotes, label="closing quote")
    valuation_index = _index_unique(valuations, label="valuation")

    seen_profiles: set[tuple[Market, str]] = set()
    result: list[MarketSnapshotRow] = []
    for profile in profiles:
        if resolved_market is not None and profile.market is not resolved_market:
            continue

        key = (profile.market, profile.code)
        if key in seen_profiles:
            raise ValueError(
                f"duplicate company-directory row for {profile.market.value} {profile.code}"
            )
        seen_profiles.add(key)

        quote = quote_index.get(key)
        valuation = valuation_index.get(key)
        result.append(
            MarketSnapshotRow(
                market=profile.market,
                code=profile.code,
                name=profile.name,
                short_name=profile.short_name,
                english_name=profile.english_name,
                industry=profile.industry,
                listing_date=profile.listing_date,
                quote_date=quote.date if quote else None,
                close=quote.close if quote else None,
                valuation_date=valuation.date if valuation else None,
                pe_ratio=valuation.pe_ratio if valuation else None,
                dividend_yield_pct=(valuation.dividend_yield_pct if valuation else None),
                price_to_book=valuation.price_to_book if valuation else None,
                dividend_per_share=(valuation.dividend_per_share if valuation else None),
            )
        )

    result.sort(key=lambda row: (row.market.value, row.code))
    return result


def fetch_market_snapshot(
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> list[MarketSnapshotRow]:
    """Fetch and join the current official listed-equity snapshot.

    ``market=None`` fetches both TWSE and TPEx. Passing a market fetches only the
    three source datasets required for that exchange.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    if market is None:
        profiles = fetch_company_directory(timeout=timeout)
        quotes = [
            *fetch_twse_closing_quotes(timeout=timeout),
            *fetch_tpex_closing_quotes(timeout=timeout),
        ]
        valuations = fetch_valuation_metrics(timeout=timeout)
        return build_market_snapshot(profiles, quotes, valuations)

    resolved = normalize_market(market)
    if resolved is Market.TWSE:
        profiles = fetch_twse_company_directory(timeout=timeout)
        quotes = fetch_twse_closing_quotes(timeout=timeout)
        valuations = fetch_twse_valuation(timeout=timeout)
    else:
        profiles = fetch_tpex_company_directory(timeout=timeout)
        quotes = fetch_tpex_closing_quotes(timeout=timeout)
        valuations = fetch_tpex_valuation(timeout=timeout)

    return build_market_snapshot(
        profiles,
        quotes,
        valuations,
        market=resolved,
    )


def summarize_market_snapshot(rows: Sequence[MarketSnapshotRow]) -> MarketSnapshotSummary:
    """Summarize source coverage without treating missing metrics as zero."""
    quote_dates = sorted({row.quote_date for row in rows if row.quote_date is not None})
    valuation_dates = sorted(
        {row.valuation_date for row in rows if row.valuation_date is not None}
    )
    with_quote = sum(row.has_quote for row in rows)
    with_valuation = sum(row.has_valuation for row in rows)
    return MarketSnapshotSummary(
        rows=len(rows),
        with_quote=with_quote,
        with_valuation=with_valuation,
        missing_quote=len(rows) - with_quote,
        missing_valuation=len(rows) - with_valuation,
        quote_dates=tuple(quote_dates),
        valuation_dates=tuple(valuation_dates),
    )


def write_market_snapshot_csv(
    rows: Iterable[MarketSnapshotRow],
    path: str | Path,
) -> Path:
    """Write a normalized joined snapshot to UTF-8 CSV."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "market",
                "code",
                "yahoo",
                "name",
                "short_name",
                "english_name",
                "industry",
                "listing_date",
                "quote_date",
                "close",
                "valuation_date",
                "pe_ratio",
                "dividend_yield_pct",
                "price_to_book",
                "dividend_per_share",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.market.value,
                    row.code,
                    row.yahoo,
                    row.name,
                    row.short_name,
                    row.english_name,
                    row.industry,
                    row.listing_date,
                    row.quote_date,
                    row.close,
                    row.valuation_date,
                    row.pe_ratio,
                    row.dividend_yield_pct,
                    row.price_to_book,
                    row.dividend_per_share,
                ]
            )
    return destination
