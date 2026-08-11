import pytest

from taiwan_market_toolkit import Market, normalize_symbol


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


def test_rejects_conflicting_market_hint():
    with pytest.raises(ValueError):
        normalize_symbol("2330.TW", "TWO")
