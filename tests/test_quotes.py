from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit.quotes import (
    ClosingQuote,
    parse_tpex_closing_quotes,
    parse_twse_closing_quotes,
)
from taiwan_market_toolkit.symbols import Market


TWSE_FIXTURE = """[
  {
    "Date": "20260811",
    "Code": "2330",
    "Name": "台積電",
    "TradeVolume": "12,345",
    "OpeningPrice": "1000",
    "HighestPrice": "1010",
    "LowestPrice": "995",
    "ClosingPrice": "1005"
  },
  {
    "Date": "20260811",
    "Code": "0000",
    "Name": "無成交測試",
    "ClosingPrice": "-"
  }
]"""

TPEX_FIXTURE = """[
  {
    "Date": "115/08/11",
    "SecuritiesCompanyCode": "6488",
    "CompanyName": "環球晶",
    "Close": "350.5"
  }
]"""


def test_parse_twse_closing_quotes():
    quotes = parse_twse_closing_quotes(TWSE_FIXTURE)

    assert quotes[0] == ClosingQuote(
        market=Market.TWSE,
        date=date(2026, 8, 11),
        code="2330",
        name="台積電",
        close=Decimal("1005"),
    )
    assert quotes[1].close is None


def test_parse_tpex_closing_quotes_supports_roc_dates():
    quotes = parse_tpex_closing_quotes(TPEX_FIXTURE)

    assert quotes[0].market is Market.TPEx
    assert quotes[0].date == date(2026, 8, 11)
    assert quotes[0].code == "6488"
    assert quotes[0].close == Decimal("350.5")


def test_quote_payload_must_be_array():
    with pytest.raises(ValueError, match="JSON array"):
        parse_twse_closing_quotes('{"Code":"2330"}')


def test_quote_rows_require_expected_schema():
    with pytest.raises(ValueError, match="ClosingPrice"):
        parse_twse_closing_quotes('[{"Date":"20260811","Code":"2330","Name":"x"}]')

    with pytest.raises(ValueError, match="SecuritiesCompanyCode"):
        parse_tpex_closing_quotes('[{"Date":"1150811","CompanyName":"x","Close":"1"}]')
