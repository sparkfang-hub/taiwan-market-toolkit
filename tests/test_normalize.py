from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit import (
    dataframe_to_ohlcv,
    infer_column_map,
    normalize_and_validate_ohlcv_records,
    normalize_ohlcv_records,
    parse_ohlcv_csv,
)


def test_infer_common_column_aliases():
    mapping = infer_column_map(
        ["Trading Date", "Open Price", "High Price", "Low Price", "Close", "Vol"]
    )
    assert mapping == {
        "date": "Trading Date",
        "open": "Open Price",
        "high": "High Price",
        "low": "Low Price",
        "close": "Close",
        "volume": "Vol",
    }


def test_infer_traditional_chinese_column_aliases():
    mapping = infer_column_map(["交易日期", "開盤價", "最高價", "最低價", "收盤價", "成交股數"])
    assert mapping == {
        "date": "交易日期",
        "open": "開盤價",
        "high": "最高價",
        "low": "最低價",
        "close": "收盤價",
        "volume": "成交股數",
    }


def test_normalize_records_sorts_and_coerces_values():
    rows = normalize_ohlcv_records(
        [
            {
                "date": "2026/08/11",
                "open": "101.5",
                "high": "110",
                "low": "100",
                "close": "108.5",
                "volume": "1,200",
            },
            {
                "date": "20260810",
                "open": 100,
                "high": 105,
                "low": 98,
                "close": 103,
                "volume": 900,
            },
        ]
    )

    assert [row.date for row in rows] == [date(2026, 8, 10), date(2026, 8, 11)]
    assert rows[1].open == Decimal("101.5")
    assert rows[1].volume == 1200


def test_normalize_traditional_chinese_csv_with_roc_dates():
    csv_text = """交易日期,開盤價,最高價,最低價,收盤價,成交股數
115/08/11,101.5,110,100,108.5,"1,200"
1150810,100,105,98,103,900
"""
    rows = parse_ohlcv_csv(csv_text)

    assert [row.date for row in rows] == [date(2026, 8, 10), date(2026, 8, 11)]
    assert rows[1].close == Decimal("108.5")
    assert rows[1].volume == 1200


def test_invalid_roc_date_is_rejected():
    with pytest.raises(ValueError, match="invalid ROC date"):
        normalize_ohlcv_records(
            [
                {
                    "日期": "115/13/40",
                    "開盤": 100,
                    "最高": 101,
                    "最低": 99,
                    "收盤": 100,
                    "成交量": 10,
                }
            ]
        )


def test_custom_column_map():
    rows = normalize_ohlcv_records(
        [
            {
                "d": "2026-08-11",
                "o": "1",
                "h": "2",
                "l": "0.5",
                "c": "1.5",
                "v": "10",
            }
        ],
        column_map={
            "date": "d",
            "open": "o",
            "high": "h",
            "low": "l",
            "close": "c",
            "volume": "v",
        },
    )
    assert rows[0].close == Decimal("1.5")


def test_parse_csv_and_validation_integration():
    csv_text = """date,open,high,low,close,volume
2026-08-11,100,99,95,98,1000
"""
    rows = parse_ohlcv_csv(csv_text)
    result = normalize_and_validate_ohlcv_records(
        [
            {
                "date": rows[0].date,
                "open": rows[0].open,
                "high": rows[0].high,
                "low": rows[0].low,
                "close": rows[0].close,
                "volume": rows[0].volume,
            }
        ]
    )
    assert any(issue.code == "invalid_high" for issue in result.issues)


def test_row_error_includes_row_number():
    with pytest.raises(ValueError, match="Row 2"):
        normalize_ohlcv_records(
            [
                {
                    "date": "2026-08-10",
                    "open": "100",
                    "high": "101",
                    "low": "99",
                    "close": "100",
                    "volume": "10",
                },
                {
                    "date": "not-a-date",
                    "open": "100",
                    "high": "101",
                    "low": "99",
                    "close": "100",
                    "volume": "10",
                },
            ]
        )


class FakeFrame:
    def to_dict(self, *, orient):
        assert orient == "records"
        return [
            {
                "date": "2026-08-11",
                "open": 100,
                "high": 110,
                "low": 90,
                "close": 105,
                "volume": 1000,
            }
        ]


def test_dataframe_adapter_without_pandas_dependency():
    rows = dataframe_to_ohlcv(FakeFrame())
    assert rows[0].date == date(2026, 8, 11)
