"""MCP registration for bounded joined-market snapshot queries."""

from __future__ import annotations

from typing import Any

from .market_query import filter_market_snapshot
from .market_snapshot import MarketSnapshotRow, fetch_market_snapshot


def _snapshot_payload(item: MarketSnapshotRow) -> dict[str, Any]:
    return {
        "market": item.market.value,
        "code": item.code,
        "yahoo": item.yahoo,
        "name": item.name,
        "short_name": item.short_name,
        "english_name": item.english_name,
        "industry": item.industry,
        "listing_date": item.listing_date.isoformat() if item.listing_date else None,
        "quote_date": item.quote_date.isoformat() if item.quote_date else None,
        "close": str(item.close) if item.close is not None else None,
        "valuation_date": (
            item.valuation_date.isoformat() if item.valuation_date else None
        ),
        "pe_ratio": str(item.pe_ratio) if item.pe_ratio is not None else None,
        "dividend_yield_pct": (
            str(item.dividend_yield_pct)
            if item.dividend_yield_pct is not None
            else None
        ),
        "price_to_book": (
            str(item.price_to_book) if item.price_to_book is not None else None
        ),
        "dividend_per_share": (
            str(item.dividend_per_share)
            if item.dividend_per_share is not None
            else None
        ),
    }


def register_market_snapshot_tools(server: Any) -> None:
    """Register bounded, read-only market snapshot query tools on an MCP server."""

    @server.tool()
    def query_official_market_snapshot(
        query: str | None = None,
        market: str | None = None,
        industry: str | None = None,
        require_quote: bool = False,
        require_valuation: bool = False,
        limit: int = 50,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Query the official joined listed-equity snapshot with a 100-row cap.

        Filtering is identity and source-coverage oriented only. Results are not
        ranked by price, valuation, return, or any other investment criterion.
        """
        if limit <= 0 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        source_rows = fetch_market_snapshot(market, timeout=timeout)
        matches = filter_market_snapshot(
            source_rows,
            query=query,
            industry=industry,
            require_quote=require_quote,
            require_valuation=require_valuation,
        )
        returned = matches[:limit]
        return {
            "source_rows": len(source_rows),
            "matches": len(matches),
            "returned": len(returned),
            "truncated": len(matches) > len(returned),
            "data": [_snapshot_payload(item) for item in returned],
        }
