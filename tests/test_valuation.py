from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.symbols import Market
from taiwan_market_toolkit.valuation import (
    ValuationMetrics,
    fetch_valuation_metrics,
    find_valuation,
    parse_tpex_valuation,
    parse_twse_valuation,
)

TWSE_FIXTURE = """[
  {
    "Date":"1150810",
    "Code":"2330",
    "Name":"台積電",
    "PEratio":"25.50",
    "DividendYield":"1.75",
    "PBratio":"6.80"
  },
  {
    "Date":"1150810",
    "Code":"1101",
    "Name":"台泥",
    "PEratio":"",
    "DividendYield":"3.26",
    "PBratio":"0.78"
  }
]"""

TPEX_FIXTURE = """[
  {
    "Date":"115/08/10",
    "SecuritiesCompanyCode":"6488",
    "CompanyName":"環球晶",
    "PriceEarningRatio":"18.20",
    "DividendPerShare":"12.5",
    "YieldRatio":"3.60",
    "PriceBookRatio":"2.10"
  }
]"""


def test_parse_twse_valuation_preserves_missing_values():
    rows = parse_twse_valuation(TWSE_FIXTURE)

    assert rows[0] == ValuationMetrics(
        market=Market.TWSE,
        date=date(2026, 8, 10),
        code="2330",
        name="台積電",
        pe_ratio=Decimal("25.50"),
        dividend_yield_pct=Decimal("1.75"),
        price_to_book=Decimal("6.80"),
        dividend_per_share=None,
    )
    assert rows[1].pe_ratio is None


def test_parse_tpex_valuation_supports_roc_dates_and_dividend_per_share():
    rows = parse_tpex_valuation(TPEX_FIXTURE)

    assert rows[0] == ValuationMetrics(
        market=Market.TPEx,
        date=date(2026, 8, 10),
        code="6488",
        name="環球晶",
        pe_ratio=Decimal("18.20"),
        dividend_yield_pct=Decimal("3.60"),
        price_to_book=Decimal("2.10"),
        dividend_per_share=Decimal("12.5"),
    )


def test_valuation_payload_must_be_array():
    with pytest.raises(ValueError, match="JSON array"):
        parse_twse_valuation('{"Code":"2330"}')


def test_valuation_rows_require_expected_schema():
    with pytest.raises(ValueError, match="PEratio"):
        parse_twse_valuation(
            '[{"Date":"1150810","Code":"2330","Name":"x","DividendYield":"1","PBratio":"1"}]'
        )

    with pytest.raises(ValueError, match="PriceEarningRatio"):
        parse_tpex_valuation(
            '[{"Date":"1150810","SecuritiesCompanyCode":"6488","CompanyName":"x","YieldRatio":"1","PriceBookRatio":"1"}]'
        )


def test_fetch_valuation_metrics_dispatches_market(monkeypatch):
    twse = parse_twse_valuation(TWSE_FIXTURE)
    tpex = parse_tpex_valuation(TPEX_FIXTURE)

    monkeypatch.setattr(
        "taiwan_market_toolkit.valuation.fetch_twse_valuation",
        lambda *, timeout: twse,
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.valuation.fetch_tpex_valuation",
        lambda *, timeout: tpex,
    )

    assert fetch_valuation_metrics("TWSE", timeout=1) == twse
    assert fetch_valuation_metrics("TPEX", timeout=1) == tpex
    assert fetch_valuation_metrics(timeout=1) == [*twse, *tpex]


def test_find_valuation_dispatches_by_suffix(monkeypatch):
    twse = parse_twse_valuation(TWSE_FIXTURE)
    tpex = parse_tpex_valuation(TPEX_FIXTURE)

    monkeypatch.setattr(
        "taiwan_market_toolkit.valuation.fetch_valuation_metrics",
        lambda market, *, timeout: twse if market is Market.TWSE else tpex,
    )

    assert find_valuation("2330.TW", timeout=1).code == "2330"
    assert find_valuation("6488.TWO", timeout=1).code == "6488"


def test_find_valuation_requires_market_for_bare_symbol():
    with pytest.raises(ValueError, match="market is required"):
        find_valuation("2330")
