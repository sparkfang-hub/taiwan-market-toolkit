from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.directory import SecurityProfile
from taiwan_market_toolkit.overview import SecurityOverview, fetch_security_overview
from taiwan_market_toolkit.quotes import ClosingQuote
from taiwan_market_toolkit.symbols import Market
from taiwan_market_toolkit.valuation import ValuationMetrics


def _profile(code: str = "2330") -> SecurityProfile:
    return SecurityProfile(
        market=Market.TWSE,
        code=code,
        name="台灣積體電路製造股份有限公司",
        short_name="台積電",
        english_name="TSMC",
        industry="24",
        listing_date=date(1994, 9, 5),
    )


def _quote(code: str = "2330") -> ClosingQuote:
    return ClosingQuote(
        market=Market.TWSE,
        date=date(2026, 8, 11),
        code=code,
        name="台積電",
        close=Decimal("1005"),
    )


def _valuation(code: str = "2330") -> ValuationMetrics:
    return ValuationMetrics(
        market=Market.TWSE,
        date=date(2026, 8, 10),
        code=code,
        name="台積電",
        pe_ratio=Decimal("25.50"),
        dividend_yield_pct=Decimal("1.75"),
        price_to_book=Decimal("6.80"),
    )


def test_security_overview_exposes_identity_without_collapsing_dates():
    overview = SecurityOverview(_profile(), _quote(), _valuation())

    assert overview.code == "2330"
    assert overview.market is Market.TWSE
    assert overview.yahoo == "2330.TW"
    assert overview.quote.date == date(2026, 8, 11)
    assert overview.valuation.date == date(2026, 8, 10)


def test_security_overview_rejects_mixed_security_components():
    with pytest.raises(ValueError, match="same market and code"):
        SecurityOverview(_profile(), _quote(), _valuation("2454"))


def test_fetch_security_overview_reuses_explicit_normalized_identity(monkeypatch):
    calls: list[tuple[str, str, Market, float]] = []

    def fake_company(value, market, *, timeout):
        calls.append(("company", value, market, timeout))
        return _profile()

    def fake_quote(value, market, *, timeout):
        calls.append(("quote", value, market, timeout))
        return _quote()

    def fake_valuation(value, market, *, timeout):
        calls.append(("valuation", value, market, timeout))
        return _valuation()

    monkeypatch.setattr("taiwan_market_toolkit.overview.find_company", fake_company)
    monkeypatch.setattr("taiwan_market_toolkit.overview.fetch_closing_quote", fake_quote)
    monkeypatch.setattr("taiwan_market_toolkit.overview.find_valuation", fake_valuation)

    result = fetch_security_overview("2330.TW", timeout=2.5)

    assert result.code == "2330"
    assert calls == [
        ("company", "2330", Market.TWSE, 2.5),
        ("quote", "2330", Market.TWSE, 2.5),
        ("valuation", "2330", Market.TWSE, 2.5),
    ]


def test_fetch_security_overview_requires_market_for_bare_symbol():
    with pytest.raises(ValueError, match="market is required"):
        fetch_security_overview("2330")
