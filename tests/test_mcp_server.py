import pytest
from mcp import Client

from taiwan_market_toolkit.mcp_server import create_mcp_server


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
