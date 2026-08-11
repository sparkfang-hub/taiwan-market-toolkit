from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.directory import SecurityProfile
from taiwan_market_toolkit.market_snapshot import (
    build_market_snapshot,
    fetch_market_snapshot,
    summarize_market_snapshot,
    write_market_snapshot_csv,
)
from taiwan_market_toolkit.quotes import ClosingQuote
from taiwan_market_toolkit.symbols import Market
from taiwan_market_toolkit.valuation import ValuationMetrics


def _profile(code: str, market: Market = Market.TWSE) -> SecurityProfile:
    return SecurityProfile(
        market=market,
        code=code,
        name=f"Company {code}",
        short_name=code,
        english_name=f"Company {code}",
        industry="24",
        listing_date=date(2000, 1, 1),
    )


def _quote(code: str, market: Market = Market.TWSE) -> ClosingQuote:
    return ClosingQuote(
        market=market,
        date=date(2026, 8, 11),
        code=code,
        name=f"Company {code}",
        close=Decimal("100.5"),
    )


def _valuation(code: str, market: Market = Market.TWSE) -> ValuationMetrics:
    return ValuationMetrics(
        market=market,
        date=date(2026, 8, 10),
        code=code,
        name=f"Company {code}",
        pe_ratio=Decimal("20.0"),
        dividend_yield_pct=Decimal("2.5"),
        price_to_book=Decimal("3.0"),
    )


def test_build_market_snapshot_uses_company_directory_as_universe():
    profiles = [_profile("2330"), _profile("2317")]
    quotes = [_quote("2330"), _quote("0050")]
    valuations = [_valuation("2330")]

    rows = build_market_snapshot(profiles, quotes, valuations)

    assert [row.code for row in rows] == ["2317", "2330"]
    by_code = {row.code: row for row in rows}
    assert by_code["2330"].close == Decimal("100.5")
    assert by_code["2330"].pe_ratio == Decimal("20.0")
    assert by_code["2330"].quote_date == date(2026, 8, 11)
    assert by_code["2330"].valuation_date == date(2026, 8, 10)
    assert by_code["2317"].has_quote is False
    assert by_code["2317"].has_valuation is False
    assert "0050" not in by_code


def test_build_market_snapshot_can_filter_one_market():
    rows = build_market_snapshot(
        [_profile("2330"), _profile("6488", Market.TPEx)],
        [_quote("2330"), _quote("6488", Market.TPEx)],
        [_valuation("2330"), _valuation("6488", Market.TPEx)],
        market="TPEX",
    )

    assert len(rows) == 1
    assert rows[0].market is Market.TPEx
    assert rows[0].code == "6488"
    assert rows[0].yahoo == "6488.TWO"


def test_build_market_snapshot_rejects_duplicate_source_rows():
    with pytest.raises(ValueError, match="duplicate closing quote"):
        build_market_snapshot(
            [_profile("2330")],
            [_quote("2330"), _quote("2330")],
            [],
        )


def test_summarize_market_snapshot_reports_source_coverage():
    rows = build_market_snapshot(
        [_profile("2330"), _profile("2317")],
        [_quote("2330")],
        [_valuation("2330"), _valuation("2317")],
    )

    summary = summarize_market_snapshot(rows)

    assert summary.rows == 2
    assert summary.with_quote == 1
    assert summary.missing_quote == 1
    assert summary.with_valuation == 2
    assert summary.missing_valuation == 0
    assert summary.quote_dates == (date(2026, 8, 11),)
    assert summary.valuation_dates == (date(2026, 8, 10),)


def test_fetch_market_snapshot_only_calls_requested_exchange(monkeypatch):
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_twse_company_directory",
        lambda *, timeout: [_profile("2330")],
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_twse_closing_quotes",
        lambda *, timeout: [_quote("2330")],
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_twse_valuation",
        lambda *, timeout: [_valuation("2330")],
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_tpex_company_directory",
        lambda **kwargs: pytest.fail("TPEx directory should not be fetched"),
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_tpex_closing_quotes",
        lambda **kwargs: pytest.fail("TPEx quotes should not be fetched"),
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.market_snapshot.fetch_tpex_valuation",
        lambda **kwargs: pytest.fail("TPEx valuation should not be fetched"),
    )

    rows = fetch_market_snapshot("TWSE", timeout=2.0)

    assert len(rows) == 1
    assert rows[0].code == "2330"
    assert rows[0].close == Decimal("100.5")


def test_write_market_snapshot_csv_preserves_dates_and_missing_values(tmp_path):
    rows = build_market_snapshot(
        [_profile("2330"), _profile("2317")],
        [_quote("2330")],
        [_valuation("2330")],
    )

    destination = write_market_snapshot_csv(rows, tmp_path / "snapshot.csv")
    text = destination.read_text(encoding="utf-8-sig")

    assert "market,code,yahoo,name,short_name" in text
    assert "TWSE,2330,2330.TW" in text
    assert "2026-08-11,100.5,2026-08-10,20.0,2.5,3.0" in text
    assert "TWSE,2317,2317.TW" in text
