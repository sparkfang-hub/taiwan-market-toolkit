from datetime import date

import pytest

from taiwan_market_toolkit import (
    Market,
    SecurityProfile,
    find_company,
    parse_tpex_company_directory,
    parse_twse_company_directory,
    search_company_directory,
)

TWSE_FIXTURE = """[
  {
    "公司代號": "2330",
    "公司名稱": "台灣積體電路製造股份有限公司",
    "公司簡稱": "台積電",
    "英文簡稱": "TSMC",
    "產業別": "24",
    "上市日期": "19940905"
  },
  {
    "公司代號": "2454",
    "公司名稱": "聯發科技股份有限公司",
    "公司簡稱": "聯發科",
    "英文簡稱": "MediaTek",
    "產業別": "24",
    "上市日期": "0900723"
  }
]"""

TPEX_FIXTURE = """[
  {
    "SecuritiesCompanyCode": "6488",
    "CompanyName": "環球晶圓股份有限公司",
    "CompanyAbbreviation": "環球晶",
    "Symbol": "GlobalWafers",
    "SecuritiesIndustryCode": "24",
    "DateOfListing": "1050926"
  }
]"""


def test_parse_twse_company_directory():
    profiles = parse_twse_company_directory(TWSE_FIXTURE)

    assert profiles[0] == SecurityProfile(
        market=Market.TWSE,
        code="2330",
        name="台灣積體電路製造股份有限公司",
        short_name="台積電",
        english_name="TSMC",
        industry="24",
        listing_date=date(1994, 9, 5),
    )
    assert profiles[0].yahoo == "2330.TW"
    assert profiles[1].listing_date == date(2001, 7, 23)


def test_parse_tpex_company_directory():
    profiles = parse_tpex_company_directory(TPEX_FIXTURE)

    assert profiles == [
        SecurityProfile(
            market=Market.TPEx,
            code="6488",
            name="環球晶圓股份有限公司",
            short_name="環球晶",
            english_name="GlobalWafers",
            industry="24",
            listing_date=date(2016, 9, 26),
        )
    ]
    assert profiles[0].yahoo == "6488.TWO"


def test_directory_search_ranks_exact_code_and_names():
    profiles = [
        *parse_twse_company_directory(TWSE_FIXTURE),
        *parse_tpex_company_directory(TPEX_FIXTURE),
    ]

    assert search_company_directory(profiles, "2330")[0].short_name == "台積電"
    assert search_company_directory(profiles, "聯發")[0].code == "2454"
    assert search_company_directory(profiles, "global")[0].code == "6488"
    assert search_company_directory(profiles, "環球", market=Market.TWSE) == []


def test_directory_search_validates_query_and_limit():
    profiles = parse_twse_company_directory(TWSE_FIXTURE)

    with pytest.raises(ValueError, match="query must not be empty"):
        search_company_directory(profiles, "   ")
    with pytest.raises(ValueError, match="limit must be positive"):
        search_company_directory(profiles, "2330", limit=0)


def test_company_directory_payload_must_be_array():
    with pytest.raises(ValueError, match="JSON array"):
        parse_twse_company_directory('{"公司代號":"2330"}')


def test_company_directory_requires_company_code():
    with pytest.raises(ValueError, match="no company code"):
        parse_tpex_company_directory('[{"CompanyName":"x"}]')


def test_find_company_dispatches_to_explicit_market(monkeypatch):
    twse = parse_twse_company_directory(TWSE_FIXTURE)
    tpex = parse_tpex_company_directory(TPEX_FIXTURE)

    monkeypatch.setattr(
        "taiwan_market_toolkit.directory.fetch_twse_company_directory",
        lambda *, timeout: twse,
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.directory.fetch_tpex_company_directory",
        lambda *, timeout: tpex,
    )

    assert find_company("2330.TW", timeout=1).short_name == "台積電"
    assert find_company("6488", "TPEX", timeout=1).short_name == "環球晶"


def test_find_company_requires_market_for_bare_symbol():
    with pytest.raises(ValueError, match="market is required"):
        find_company("2330")
