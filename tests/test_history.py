from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit import history
from taiwan_market_toolkit.symbols import Market


TWSE_PAYLOAD = """{
  "stat": "OK",
  "date": "20260801",
  "data": [
    ["115/08/10", "1,234,000", "1,245,000,000", "1000", "1020", "995", "1010", "+10", "8,765"],
    ["115/08/11", "2,000,000", "2,050,000,000", "1010", "1040", "1005", "1030", "+20", "9,000"]
  ]
}"""

TPEX_PAYLOAD = """{
  "tables": [{
    "title": "個股日成交資訊",
    "date": "20260801",
    "fields": ["日期", "成交張數", "成交仟元", "開盤", "最高", "最低", "收盤", "漲跌", "筆數"],
    "data": [
      ["115/08/10", "1,234", "432,100", "350.0", "355.0", "348.0", "352.5", "2.5", "4,321"],
      ["115/08/11", "2,000", "710,000", "352.5", "360.0", "351.0", "358.0", "5.5", "5,000"]
    ]
  }],
  "date": "20260801",
  "code": "6488",
  "stat": "ok"
}"""


def test_parse_twse_history_normalizes_month_rows():
    prices = history.parse_twse_history(TWSE_PAYLOAD, "2330")

    assert len(prices) == 2
    assert prices[0] == history.HistoricalPrice(
        market=Market.TWSE,
        code="2330",
        date=date(2026, 8, 10),
        open=Decimal("1000"),
        high=Decimal("1020"),
        low=Decimal("995"),
        close=Decimal("1010"),
        volume=1_234_000,
        trade_value=1_245_000_000,
        change=Decimal("10"),
        transactions=8_765,
        source="TWSE exchangeReport/STOCK_DAY",
    )


def test_parse_tpex_history_converts_common_stock_lots_and_thousands():
    prices = history.parse_tpex_history(TPEX_PAYLOAD, "6488")

    assert prices[0].market is Market.TPEx
    assert prices[0].date == date(2026, 8, 10)
    assert prices[0].volume == 1_234_000
    assert prices[0].trade_value == 432_100_000
    assert prices[0].close == Decimal("352.5")
    assert prices[0].transactions == 4_321


def test_history_rejects_non_equity_code_to_avoid_wrong_lot_conversion():
    with pytest.raises(ValueError, match="four-digit"):
        history.parse_tpex_history(TPEX_PAYLOAD, "00679B")


def test_history_parser_returns_empty_for_official_no_data_message():
    assert history.parse_twse_history('{"stat":"很抱歉，沒有符合條件的資料!"}', "2330") == []
    assert history.parse_tpex_history('{"stat":"查無資料","tables":[]}', "6488") == []


def test_history_parser_detects_schema_drift():
    with pytest.raises(history.HistoricalPriceError, match="schema may have changed"):
        history.parse_twse_history('{"stat":"OK","data":[["bad"]]}', "2330")


def test_history_to_ohlcv_skips_incomplete_rows_by_default():
    complete, incomplete = history.parse_twse_history(TWSE_PAYLOAD, "2330")
    incomplete = history.HistoricalPrice(
        market=incomplete.market,
        code=incomplete.code,
        date=incomplete.date,
        open=None,
        high=incomplete.high,
        low=incomplete.low,
        close=incomplete.close,
        volume=incomplete.volume,
        trade_value=incomplete.trade_value,
        change=incomplete.change,
        transactions=incomplete.transactions,
        source=incomplete.source,
    )

    rows = history.history_to_ohlcv([complete, incomplete])
    assert len(rows) == 1
    assert rows[0].date == date(2026, 8, 10)

    with pytest.raises(ValueError, match="incomplete OHLC"):
        history.history_to_ohlcv([incomplete], strict=True)


def test_fetch_price_history_dispatches_months_filters_and_sorts(monkeypatch):
    calls = []

    def fake_fetch(code, month, *, timeout):
        calls.append((code, month, timeout))
        if month.month == 7:
            return [
                history.HistoricalPrice(
                    Market.TWSE,
                    "2330",
                    date(2026, 7, 31),
                    Decimal("900"),
                    Decimal("910"),
                    Decimal("890"),
                    Decimal("905"),
                    100,
                    1000,
                    Decimal("5"),
                    10,
                    "fixture",
                )
            ]
        return [
            history.HistoricalPrice(
                Market.TWSE,
                "2330",
                date(2026, 8, 3),
                Decimal("910"),
                Decimal("920"),
                Decimal("905"),
                Decimal("915"),
                200,
                2000,
                Decimal("10"),
                20,
                "fixture",
            )
        ]

    monkeypatch.setattr("taiwan_market_toolkit.history.fetch_twse_history_month", fake_fetch)
    monkeypatch.setattr("taiwan_market_toolkit.history.time.sleep", lambda _: None)

    prices = history.fetch_price_history(
        "2330.TW",
        start=date(2026, 7, 30),
        end=date(2026, 8, 3),
        timeout=2,
        request_interval=0,
    )

    assert [item.date for item in prices] == [date(2026, 7, 31), date(2026, 8, 3)]
    assert [call[1] for call in calls] == [date(2026, 7, 1), date(2026, 8, 1)]


def test_fetch_price_history_requires_market_for_bare_ticker():
    with pytest.raises(ValueError, match="market is required"):
        history.fetch_price_history(
            "2330",
            start=date(2026, 8, 1),
            end=date(2026, 8, 31),
        )


def test_fetch_price_history_caps_request_span():
    with pytest.raises(ValueError, match="max_months"):
        history.fetch_price_history(
            "2330.TW",
            start=date(2020, 1, 1),
            end=date(2021, 1, 1),
            max_months=12,
        )


def test_write_history_csv_preserves_normalized_values(tmp_path):
    prices = history.parse_twse_history(TWSE_PAYLOAD, "2330")
    destination = history.write_history_csv(prices, tmp_path / "nested" / "history.csv")

    text = destination.read_text(encoding="utf-8-sig")
    assert "date,market,code,open,high,low,close,volume" in text
    assert "2026-08-10,TWSE,2330,1000,1020,995,1010,1234000" in text
