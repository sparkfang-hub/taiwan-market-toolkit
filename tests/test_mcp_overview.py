from datetime import date
from decimal import Decimal

import pytest
from mcp import Client

from taiwan_market_toolkit import (
    ClosingQuote,
    Market,
    SecurityOverview,
    SecurityProfile,
    ValuationMetrics,
)
from taiwan_market_toolkit.mcp_server import create_mcp_server


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_official_security_overview(monkeypatch):
    overview = SecurityOverview(
        profile=SecurityProfile(
            market=Market.TWSE,
            code="2330",
            name="台灣積體電路製造股份有限公司",
            short_name="台積電",
            english_name="TSMC",
            industry="24",
            listing_date=date(1994, 9, 5),
        ),
        quote=ClosingQuote(
            market=Market.TWSE,
            date=date(2026, 8, 11),
            code="2330",
            name="台積電",
            close=Decimal("1005"),
        ),
        valuation=ValuationMetrics(
            market=Market.TWSE,
            date=date(2026, 8, 10),
            code="2330",
            name="台積電",
            pe_ratio=Decimal("25.50"),
            dividend_yield_pct=Decimal("1.75"),
            price_to_book=Decimal("6.80"),
        ),
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.mcp_server.fetch_security_overview",
        lambda value, market, *, timeout: overview,
    )

    async with Client(create_mcp_server(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_official_security_overview",
            {"value": "2330.TW"},
        )

    assert not result.is_error
    assert result.structured_content["code"] == "2330"
    assert result.structured_content["profile"]["short_name"] == "台積電"
    assert result.structured_content["quote"]["date"] == "2026-08-11"
    assert result.structured_content["valuation"]["date"] == "2026-08-10"
    assert result.structured_content["valuation"]["pe_ratio"] == "25.50"
