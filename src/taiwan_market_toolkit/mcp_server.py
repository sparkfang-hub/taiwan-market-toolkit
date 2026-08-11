"""Optional Model Context Protocol server for Taiwan Market Toolkit.

Install with ``taiwan-market-toolkit[mcp]``. The core package remains usable
without the MCP SDK.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .analytics import (
    daily_returns,
    exponential_moving_average,
    simple_moving_average,
    summarize_ohlcv,
)
from .calendar import TaiwanTradingCalendar
from .directory import (
    SecurityProfile,
    fetch_company_directory,
    find_company,
    search_company_directory,
)
from .normalize import parse_ohlcv_csv
from .quotes import fetch_closing_quote
from .symbols import normalize_market, normalize_symbol
from .twse import fetch_twse_calendar
from .validation import validate_ohlcv
from .valuation import ValuationMetrics, find_valuation


def _profile_payload(profile: SecurityProfile) -> dict[str, Any]:
    return {
        "code": profile.code,
        "market": profile.market.value,
        "yahoo": profile.yahoo,
        "name": profile.name,
        "short_name": profile.short_name,
        "english_name": profile.english_name,
        "industry": profile.industry,
        "listing_date": profile.listing_date.isoformat() if profile.listing_date else None,
    }


def _valuation_payload(metrics: ValuationMetrics) -> dict[str, Any]:
    return {
        "date": metrics.date.isoformat(),
        "code": metrics.code,
        "name": metrics.name,
        "market": metrics.market.value,
        "pe_ratio": str(metrics.pe_ratio) if metrics.pe_ratio is not None else None,
        "dividend_yield_pct": (
            str(metrics.dividend_yield_pct) if metrics.dividend_yield_pct is not None else None
        ),
        "price_to_book": (
            str(metrics.price_to_book) if metrics.price_to_book is not None else None
        ),
        "dividend_per_share": (
            str(metrics.dividend_per_share) if metrics.dividend_per_share is not None else None
        ),
    }


def create_mcp_server():
    """Create the optional MCP server using the official MCP Python SDK."""
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover - exercised by packaging users
        raise RuntimeError(
            "MCP support is optional. Install with: pip install 'taiwan-market-toolkit[mcp]'"
        ) from exc

    server = MCPServer(
        "Taiwan Market Toolkit",
        version="0.1.0",
        instructions=(
            "Utilities for Taiwan market symbols, official company metadata, read-only "
            "closing quotes and valuation metrics, trading calendars, OHLCV data quality, "
            "and strategy-neutral descriptive analytics. This server does not provide "
            "trading signals, recommendations, or order execution."
        ),
    )

    @server.tool()
    def normalize_taiwan_symbol(value: str, market: str | None = None) -> dict[str, Any]:
        """Normalize a Taiwan security ticker and return its market representation."""
        result = normalize_symbol(value, market)
        return {
            "code": result.code,
            "market": result.market.value if result.market else None,
            "yahoo": result.yahoo,
        }

    @server.tool()
    def get_official_company_profile(
        value: str,
        market: str | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Fetch one company profile from the official TWSE or TPEx directory."""
        return _profile_payload(find_company(value, market, timeout=timeout))

    @server.tool()
    def search_official_company_directory(
        query: str,
        market: str | None = None,
        limit: int = 20,
        timeout: float = 10.0,
    ) -> list[dict[str, Any]]:
        """Search official TWSE/TPEx company identity metadata by code or name."""
        profiles = fetch_company_directory(timeout=timeout)
        resolved_market = normalize_market(market) if market else None
        return [
            _profile_payload(profile)
            for profile in search_company_directory(
                profiles,
                query,
                market=resolved_market,
                limit=limit,
            )
        ]

    @server.tool()
    def get_official_closing_quote(
        value: str,
        market: str | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Fetch a read-only closing quote from the relevant official exchange OpenAPI."""
        result = fetch_closing_quote(value, market, timeout=timeout)
        return {
            "date": result.date.isoformat(),
            "code": result.code,
            "name": result.name,
            "market": result.market.value,
            "close": str(result.close) if result.close is not None else None,
        }

    @server.tool()
    def get_official_valuation_metrics(
        value: str,
        market: str | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Fetch official P/E, dividend yield, and P/B metrics for one security."""
        return _valuation_payload(find_valuation(value, market, timeout=timeout))

    @server.tool()
    def check_trading_day(
        day: str,
        closures: list[str] | None = None,
        openings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Check a date using weekend rules plus caller-supplied market overrides."""
        target = date.fromisoformat(day)
        calendar = TaiwanTradingCalendar.from_overrides(
            closures=[date.fromisoformat(value) for value in closures or []],
            openings=[date.fromisoformat(value) for value in openings or []],
        )
        return {
            "date": target.isoformat(),
            "trading_day": calendar.is_trading_day(target),
            "source": "weekend-rules-plus-explicit-overrides",
        }

    @server.tool()
    def check_twse_trading_day(day: str) -> dict[str, Any]:
        """Check a date against the official TWSE OpenAPI holiday schedule."""
        target = date.fromisoformat(day)
        calendar = fetch_twse_calendar()
        return {
            "date": target.isoformat(),
            "trading_day": calendar.is_trading_day(target),
            "source": "TWSE OpenAPI holidaySchedule/holidaySchedule",
        }

    @server.tool()
    def validate_ohlcv_csv_text(
        csv_text: str,
        preserve_order: bool = False,
    ) -> dict[str, Any]:
        """Normalize CSV-formatted OHLCV data and report data-quality issues."""
        rows = parse_ohlcv_csv(csv_text, sort=not preserve_order)
        issues = validate_ohlcv(rows)
        return {
            "rows": len(rows),
            "valid": not issues,
            "issues": [
                {
                    "row": issue.row,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in issues
            ],
        }

    @server.tool()
    def analyze_ohlcv_csv_text(
        csv_text: str,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
    ) -> dict[str, Any]:
        """Return descriptive OHLCV statistics and caller-selected moving averages."""
        rows = parse_ohlcv_csv(csv_text)
        summary = summarize_ohlcv(rows)
        returns = daily_returns(rows)

        sma: dict[str, str | None] = {}
        for window in sma_windows or []:
            points = simple_moving_average(rows, window)
            sma[str(window)] = str(points[-1].value) if points else None

        ema: dict[str, str | None] = {}
        for window in ema_windows or []:
            points = exponential_moving_average(rows, window)
            ema[str(window)] = str(points[-1].value) if points else None

        return {
            "rows": summary.rows,
            "start": summary.start.isoformat() if summary.start else None,
            "end": summary.end.isoformat() if summary.end else None,
            "min_close": str(summary.min_close) if summary.min_close is not None else None,
            "max_close": str(summary.max_close) if summary.max_close is not None else None,
            "total_volume": summary.total_volume,
            "latest_return": str(returns[-1].value) if returns else None,
            "sma": sma,
            "ema": ema,
        }

    @server.resource("taiwan-market://about")
    def about() -> str:
        """Describe the scope and safety boundary of the toolkit."""
        return (
            "Taiwan Market Toolkit provides non-strategy infrastructure for Taiwan market "
            "symbol normalization, official company identity metadata, read-only closing "
            "quotes and valuation metrics, exchange-calendar queries, OHLCV data validation, "
            "and descriptive analytics. It does not provide investment advice, trading "
            "signals, or order execution."
        )

    return server


def main() -> None:
    """Run the MCP server over stdio for local AI hosts."""
    create_mcp_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
