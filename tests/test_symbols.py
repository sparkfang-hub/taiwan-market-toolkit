import pytest

from taiwan_market_toolkit import Market, normalize_market, normalize_symbol


def test_normalizes_twse_suffix():
    symbol = normalize_symbol("2330.TW")
    assert symbol.code == "2330"
    assert symbol.market is Market.TWSE
    assert symbol.yahoo == "2330.TW"


def test_normalizes_tpex_suffix():
    symbol = normalize_symbol("6488.TWO")
    assert symbol.market is Market.TPEx
    assert symbol.yahoo == "6488.TWO"


def test_market_hint_for_bare_symbol():
    symbol = normalize_symbol("2330", "TWSE")
    assert symbol.yahoo == "2330.TW"


def test_normalize_market_aliases():
    assert normalize_market("TWSE") is Market.TWSE
    assert normalize_market("tw") is Market.TWSE
    assert normalize_market("TPEx") is Market.TPEx
    assert normalize_market("TPEX") is Market.TPEx
    assert normalize_market("TWO") is Market.TPEx
    assert normalize_market("OTC") is Market.TPEx


def test_rejects_unknown_market_alias():
    with pytest.raises(ValueError, match="Unsupported market"):
        normalize_market("NASDAQ")


def test_rejects_conflicting_market_hint():
    with pytest.raises(ValueError):
        normalize_symbol("2330.TW", "TWO")
