from datetime import date

import pytest

from taiwan_market_toolkit import (
    calendar_from_twse_records,
    parse_roc_date,
    parse_twse_holiday_payload,
)


FIXTURE = """[
  {"Name":"中華民國開國紀念日","Date":"1150101","Weekday":"四","Description":"依規定放假1日。"},
  {"Name":"國曆新年開始交易日","Date":"1150102","Weekday":"五","Description":"國曆新年開始交易。"},
  {"Name":"農曆春節前最後交易日","Date":"1150211","Weekday":"三","Description":"農曆春節前最後交易。"},
  {"Name":"市場無交易，僅辦理結算交割作業","Date":"1150212","Weekday":"四","Description":""},
  {"Name":"農曆春節後開始交易日","Date":"1150223","Weekday":"一","Description":"農曆春節後開始交易。"}
]"""


def test_parse_roc_date():
    assert parse_roc_date("1150101") == date(2026, 1, 1)


def test_parse_roc_date_rejects_invalid_input():
    with pytest.raises(ValueError):
        parse_roc_date("2026-01-01")


def test_parse_twse_payload_classifies_open_and_closed_records():
    records = parse_twse_holiday_payload(FIXTURE)
    assert records[0].market_closed
    assert records[1].market_open
    assert records[2].market_open
    assert records[3].market_closed


def test_calendar_from_twse_records_matches_known_2026_schedule():
    calendar = calendar_from_twse_records(parse_twse_holiday_payload(FIXTURE))

    assert not calendar.is_trading_day(date(2026, 1, 1))
    assert calendar.is_trading_day(date(2026, 1, 2))
    assert calendar.is_trading_day(date(2026, 2, 11))
    assert not calendar.is_trading_day(date(2026, 2, 12))
    assert calendar.is_trading_day(date(2026, 2, 23))


def test_parse_payload_requires_array():
    with pytest.raises(ValueError, match="JSON array"):
        parse_twse_holiday_payload('{"Name":"not-an-array"}')
