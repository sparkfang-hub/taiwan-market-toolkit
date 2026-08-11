from datetime import date
from decimal import Decimal

import pytest
from mcp import Client

from taiwan_market_toolkit.mcp_server import create_mcp_server
from taiwan_market_toolkit.quotes import ClosingQuote
from taiwan_market_toolkit.symbols import Market


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def mcp_client():
    async with Client(create_mcp_server(), raise_exceptions=True) as client:
        yield client


@pytest.mark.anyio
async def test_mcp_normalize_symbol(mcp_client):
    result = await mcp_client.call_tool(
        "normalize_taiwan_symbol",
        {"value": "2330.TW"},
    )
    assert not result.is_error
    assert result.structured_content["code"] == "2330"
    assert result.structured_content["market"] == "TWSE"


@pytest.mark.anyio
async def test_mcp_official_closing_quote(mcp_client, monkeypatch):
    def fake_fetch(value, market, *, timeout):
        assert value == "2330.TW"
        assert market is None
        assert timeout == 2.0
        return ClosingQuote(
            market=Market.TWSE,
            date=date(2026, 8, 11),
            code="2330",
            name="台積電",
            close=Decimal("1005"),
        )

    monkeypatch.setattr("taiwan_market_toolkit.mcp_server.fetch_closing_quote", fake_fetch)

    result = await mcp_client.call_tool(
        "get_official_closing_quote",
        {"value": "2330.TW", "timeout": 2.0},
    )

    assert not result.is_error
    assert result.structured_content == {
        "date": "2026-08-11",
        "code": "2330",
        "name": "台積電",
        "market": "TWSE",
        "close": "1005",
    }


@pytest.mark.anyio
async def test_mcp_trading_day_override(mcp_client):
    result = await mcp_client.call_tool(
        "check_trading_day",
        {
            "day": "2026-08-09",
            "openings": ["2026-08-09"],
        },
    )
    assert not result.is_error
    assert result.structured_content["trading_day"] is True


@pytest.mark.anyio
async def test_mcp_validate_csv(mcp_client):
    csv_text = """date,open,high,low,close,volume
2026-08-11,100,99,95,98,1000
"""
    result = await mcp_client.call_tool(
        "validate_ohlcv_csv_text",
        {"csv_text": csv_text},
    )
    assert not result.is_error
    assert result.structured_content["valid"] is False
    assert result.structured_content["issues"][0]["code"] == "invalid_high"


@pytest.mark.anyio
async def test_mcp_analyze_csv(mcp_client):
    csv_text = """交易日期,開盤價,最高價,最低價,收盤價,成交股數
115/08/10,100,100,100,100,10
115/08/11,110,110,110,110,20
115/08/12,121,121,121,121,30
"""
    result = await mcp_client.call_tool(
        "analyze_ohlcv_csv_text",
        {
            "csv_text": csv_text,
            "sma_windows": [2],
            "ema_windows": [2],
        },
    )
    assert not result.is_error
    assert result.structured_content["rows"] == 3
    assert result.structured_content["latest_return"] == "0.1"
    assert result.structured_content["sma"]["2"] == "115.5"
    assert result.structured_content["ema"]["2"] == "115.6666666666666666666666667"
