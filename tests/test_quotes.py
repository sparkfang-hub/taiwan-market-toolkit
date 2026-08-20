from datetime import date
from decimal import Decimal
from http.client import IncompleteRead

import pytest

from taiwan_market_toolkit import ClosingQuote, Market
from taiwan_market_toolkit.quotes import (
    fetch_closing_quote,
    fetch_tpex_closing_payload,
    parse_tpex_closing_quotes,
    parse_twse_closing_quotes,
)

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


class _FakeResponse:
    def __init__(self, *, payload: bytes = b"", error: Exception | None = None):
        self.payload = payload
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        if self.error is not None:
            raise self.error
        return self.payload


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


def test_tpex_closing_payload_retries_truncated_http_body(monkeypatch):
    responses = iter(
        [
            _FakeResponse(error=IncompleteRead(b"partial", 10)),
            _FakeResponse(payload=b"[]"),
        ]
    )
    calls = 0

    def fake_urlopen(request, *, timeout):
        nonlocal calls
        calls += 1
        assert timeout == 2.0
        return next(responses)

    monkeypatch.setattr("taiwan_market_toolkit.quotes.urlopen", fake_urlopen)

    assert fetch_tpex_closing_payload(timeout=2.0) == b"[]"
    assert calls == 2


def test_fetch_closing_quote_dispatches_by_suffix(monkeypatch):
    twse_quote = parse_twse_closing_quotes(TWSE_FIXTURE)[0]
    tpex_quote = parse_tpex_closing_quotes(TPEX_FIXTURE)[0]

    monkeypatch.setattr(
        "taiwan_market_toolkit.quotes.fetch_twse_closing_quotes",
        lambda *, timeout: [twse_quote],
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.quotes.fetch_tpex_closing_quotes",
        lambda *, timeout: [tpex_quote],
    )

    assert fetch_closing_quote("2330.TW", timeout=1).code == "2330"
    assert fetch_closing_quote("6488.TWO", timeout=1).code == "6488"


def test_fetch_closing_quote_requires_market_for_bare_symbol():
    with pytest.raises(ValueError, match="market is required"):
        fetch_closing_quote("2330")


def test_quote_payload_must_be_array():
    with pytest.raises(ValueError, match="JSON array"):
        parse_twse_closing_quotes('{"Code":"2330"}')


def test_quote_rows_require_expected_schema():
    with pytest.raises(ValueError, match="ClosingPrice"):
        parse_twse_closing_quotes('[{"Date":"20260811","Code":"2330","Name":"x"}]')

    with pytest.raises(ValueError, match="SecuritiesCompanyCode"):
        parse_tpex_closing_quotes('[{"Date":"1150811","CompanyName":"x","Close":"1"}]')
