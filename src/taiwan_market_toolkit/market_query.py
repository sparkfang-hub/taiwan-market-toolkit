"""Deterministic, strategy-neutral filtering for joined market snapshots."""

from __future__ import annotations

from collections.abc import Sequence

from .market_snapshot import MarketSnapshotRow
from .symbols import Market, normalize_market


def filter_market_snapshot(
    rows: Sequence[MarketSnapshotRow],
    *,
    query: str | None = None,
    market: Market | str | None = None,
    industry: str | None = None,
    require_quote: bool = False,
    require_valuation: bool = False,
    limit: int | None = None,
) -> list[MarketSnapshotRow]:
    """Filter a joined snapshot without introducing investment ranking logic.

    Text matching follows identity-oriented ordering only: exact code, code prefix,
    exact company name, then name substring. Industry matching is exact after
    whitespace/case normalization because the current company directory commonly
    preserves exchange industry codes rather than inferred labels.
    """
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")

    resolved_market = normalize_market(market) if market is not None else None

    needle: str | None = None
    if query is not None:
        needle = query.strip().casefold()
        if not needle:
            raise ValueError("query must not be empty")

    industry_needle: str | None = None
    if industry is not None:
        industry_needle = industry.strip().casefold()
        if not industry_needle:
            raise ValueError("industry must not be empty")

    ranked: list[tuple[int, str, str, MarketSnapshotRow]] = []
    for row in rows:
        if resolved_market is not None and row.market is not resolved_market:
            continue
        if industry_needle is not None:
            if row.industry is None or row.industry.strip().casefold() != industry_needle:
                continue
        if require_quote and not row.has_quote:
            continue
        if require_valuation and not row.has_valuation:
            continue

        rank = 0
        if needle is not None:
            code = row.code.casefold()
            names = [row.name, row.short_name, row.english_name]
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

        ranked.append((rank, row.market.value, row.code, row))

    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    result = [item[3] for item in ranked]
    return result[:limit] if limit is not None else result
