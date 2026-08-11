from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.market_query import filter_market_snapshot
from taiwan_market_toolkit.market_snapshot import MarketSnapshotRow
from taiwan_market_toolkit.symbols import Market


def _row(
    code: str,
    *,
    market: Market = Market.TWSE,
    short_name: str | None = None,
    english_name: str | None = None,
    industry: str | None = "24",
    has_quote: bool = True,
    has_valuation: bool = True,
) -> MarketSnapshotRow:
    return MarketSnapshotRow(
        market=market,
        code=code,
        name=short_name or f"Company {code}",
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


def test_filter_market_snapshot_ranks_identity_matches():
    rows = [
        _row("2331", short_name="Other"),
        _row("9999", short_name="2330 Holdings"),
        _row("2330", short_name="台積電", english_name="TSMC"),
    ]

    matches = filter_market_snapshot(rows, query="2330")

    assert [row.code for row in matches] == ["2330", "9999"]


def test_filter_market_snapshot_matches_english_name_case_insensitively():
    rows = [
        _row("2330", short_name="台積電", english_name="TSMC"),
        _row("6488", market=Market.TPEx, short_name="環球晶", english_name="GlobalWafers"),
    ]

    matches = filter_market_snapshot(rows, query="global")

    assert [row.code for row in matches] == ["6488"]


def test_filter_market_snapshot_applies_market_industry_and_coverage_requirements():
    rows = [
        _row("2330", industry="24", has_quote=True, has_valuation=True),
        _row("2317", industry="24", has_quote=False, has_valuation=True),
        _row("1101", industry="01", has_quote=True, has_valuation=True),
        _row(
            "6488",
            market=Market.TPEx,
            industry="24",
            has_quote=True,
            has_valuation=True,
        ),
    ]

    matches = filter_market_snapshot(
        rows,
        market="TWSE",
        industry="24",
        require_quote=True,
        require_valuation=True,
    )

    assert [row.code for row in matches] == ["2330"]


def test_filter_market_snapshot_limit_is_deterministic():
    rows = [_row("3000"), _row("1000"), _row("2000")]

    matches = filter_market_snapshot(rows, limit=2)

    assert [row.code for row in matches] == ["1000", "2000"]


def test_filter_market_snapshot_rejects_blank_filters_and_bad_limit():
    rows = [_row("2330")]

    with pytest.raises(ValueError, match="query must not be empty"):
        filter_market_snapshot(rows, query="   ")
    with pytest.raises(ValueError, match="industry must not be empty"):
        filter_market_snapshot(rows, industry="   ")
    with pytest.raises(ValueError, match="limit must be positive"):
        filter_market_snapshot(rows, limit=0)
