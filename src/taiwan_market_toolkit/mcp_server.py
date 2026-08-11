"""Optional Model Context Protocol server for Taiwan Market Toolkit.

Install with ``taiwan-market-toolkit[mcp]``. The core package remains usable
without the MCP SDK.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .calendar import TaiwanTradingCalendar
from .normalize import parse_ohlcv_csv
from .symbols import normalize_symbol
from .twse import fetch_twse_calendar
from .validation import validate_ohlcv


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
            "Utilities for Taiwan market symbols, trading calendars, and OHLCV data quality. "
            "This server does not provide trading signals, recommendations, or order execution."
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

    @server.resource("taiwan-market://about")
    def about() -> str:
        """Describe the scope and safety boundary of the toolkit."""
        return (
            "Taiwan Market Toolkit provides non-strategy infrastructure for Taiwan market "
            "symbol normalization, exchange-calendar queries, and OHLCV data validation. "
            "It does not provide investment advice, trading signals, or order execution."
        )

    return server


def main() -> None:
    """Run the MCP server over stdio for local AI hosts."""
    create_mcp_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
