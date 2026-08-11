from datetime import date
from decimal import Decimal

import pytest
from mcp import Client

from taiwan_market_toolkit.market_snapshot import MarketSnapshotRow
from taiwan_market_toolkit.mcp_server import create_mcp_server
from taiwan_market_toolkit.symbols import Market


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def mcp_client():
    async with Client(create_mcp_server(), raise_exceptions=True) as client:
        yield client


def _row(
    code: str,
    *,
    market: Market = Market.TWSE,
    short_name: str,
    english_name: str,
    industry: str = "24",
    has_quote: bool = True,
    has_valuation: bool = True,
) -> MarketSnapshotRow:
    return MarketSnapshotRow(
        market=market,
        code=code,
        name=short_name,
        short_name=short_name,
        english_name=english_name,
        industry=industry,
        listing_date=date(2000, 1, 1),
        quote_date=date(2026, 8, 11) if has_quote else None,
        close=Decimal("100") if has_quote else None,
        valuation_date=date(2026, 8, 10) if has_valuation else None,
        pe_ratio=Decimal("20") if has_valuation else None,
        dividend_yield_pct=Decimal("2") if has_valuation else None,
        price_to_book=Decimal("3") if has_valuation else None,
        dividend_per_share=None,
    )


@pytest.mark.anyio
async def test_mcp_market_snapshot_query_filters_and_serializes(mcp_client, monkeypatch):
    rows = [
        _row("2330", short_name="台積電", english_name="TSMC"),
        _row(
            "6488",
            market=Market.TPEx,
            short_name="環球晶",
            english_name="GlobalWafers",
        ),
    ]

    def fake_fetch(market, *, timeout):
        assert market == "TPEX"
        assert timeout == 2.0
        return rows

    monkeypatch.setattr(
        "taiwan_market_toolkit.mcp_market.fetch_market_snapshot",
        fake_fetch,
    )

    result = await mcp_client.call_tool(
        "query_official_market_snapshot",
        {
            "query": "global",
            "market": "TPEX",
            "require_quote": True,
            "require_valuation": True,
            "limit": 10,
            "timeout": 2.0,
        },
    )

    assert not result.is_error
    assert result.structured_content["source_rows"] == 2
    assert result.structured_content["matches"] == 1
    assert result.structured_content["returned"] == 1
    assert result.structured_content["truncated"] is False
    item = result.structured_content["data"][0]
    assert item["code"] == "6488"
    assert item["market"] == "TPEx"
    assert item["yahoo"] == "6488.TWO"
    assert item["close"] == "100"
    assert item["valuation_date"] == "2026-08-10"


@pytest.mark.anyio
async def test_mcp_market_snapshot_query_enforces_row_cap(mcp_client):
    result = await mcp_client.call_tool(
        "query_official_market_snapshot",
        {"limit": 101},
    )

    assert result.is_error
