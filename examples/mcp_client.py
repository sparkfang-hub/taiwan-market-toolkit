"""Call Taiwan Market Toolkit MCP tools in memory.

Install the optional dependency first:
    python -m pip install -e '.[mcp]'
"""

import asyncio

from mcp import Client

from taiwan_market_toolkit.mcp_server import create_mcp_server


async def main() -> None:
    async with Client(create_mcp_server(), raise_exceptions=True) as client:
        symbol = await client.call_tool(
            "normalize_taiwan_symbol",
            {"value": "2330.TW"},
        )
        print(symbol.structured_content)

        trading_day = await client.call_tool(
            "check_trading_day",
            {"day": "2026-08-11"},
        )
        print(trading_day.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
