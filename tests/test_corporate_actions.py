from datetime import date
from decimal import Decimal

import pytest

from taiwan_market_toolkit import corporate_actions
from taiwan_market_toolkit.corporate_actions import (
    CorporateAction,
    CorporateActionKind,
    filter_corporate_actions,
    parse_tpex_corporate_actions,
    parse_twse_corporate_actions,
    write_corporate_actions_csv,
)
from taiwan_market_toolkit.symbols import Market


TWSE_PAYLOAD = """[
  {
    "Date": "1150819",
    "Code": "2496",
    "Name": "卓越",
    "Exdividend": "權息",
    "StockDividendRatio": "0.05000000",
    "SubscriptionRatio": "",
    "SubscriptionPricePerShare": "",
    "CashDividend": "1.500000",
    "SharesOffered": "",
    "SharesEmpOwner": "",
    "SharesholderOwner": "",
    "StockHoldingRatio": ""
  },
  {
    "Date": "1150820",
    "Code": "4764",
    "Name": "雙鍵",
    "Exdividend": "權",
    "StockDividendRatio": "",
    "SubscriptionRatio": "0.07014093",
    "SubscriptionPricePerShare": "尚未公告",
    "CashDividend": "0",
    "SharesOffered": "600000.00",
    "SharesEmpOwner": "900000.00",
    "SharesholderOwner": "4500000.00",
    "StockHoldingRatio": "52.60569940"
  }
]"""

TPEX_PAYLOAD = """[
  {
    "ExRrightsExDividendDate": "1150803",
    "SecuritiesCompanyCode": "3306",
    "CompanyName": "鼎天",
    "ExRrightsExDividend": "除息",
    "StockDividendRatio": "0.00000000",
    "SubscriptionRatioToNewSharesIssued": "0.00000000",
    "SubscriptionPricePerShare": "0.00",
    "CashDividend": "1.70000000",
    "AllocatedForPublicUnderwriting": "0",
    "SubscribedByEmployees": "0",
    "SubscribedByExistingShareholders": "0",
    "SubscribedProRataInThousandShares": "0.00000000"
  }
]"""


def test_parse_twse_corporate_actions():
    rows = parse_twse_corporate_actions(TWSE_PAYLOAD)

    assert len(rows) == 2
    first = rows[0]
    assert first.market is Market.TWSE
    assert first.date == date(2026, 8, 19)
    assert first.code == "2496"
    assert first.yahoo == "2496.TW"
    assert first.kind is CorporateActionKind.EX_RIGHTS_DIVIDEND
    assert first.stock_dividend_ratio == Decimal("0.05000000")
    assert first.cash_dividend_per_share == Decimal("1.500000")
    assert first.subscription_ratio is None

    second = rows[1]
    assert second.kind is CorporateActionKind.EX_RIGHTS
    assert second.subscription_ratio == Decimal("0.07014093")
    assert second.subscription_price_per_share is None
    assert second.cash_dividend_per_share == Decimal("0")
    assert second.public_underwriting_shares == 600000
    assert second.employee_subscription_shares == 900000
    assert second.existing_shareholder_subscription_shares == 4500000
    assert second.existing_shareholder_subscription_per_thousand == Decimal("52.60569940")


def test_parse_tpex_corporate_actions():
    rows = parse_tpex_corporate_actions(TPEX_PAYLOAD)

    assert len(rows) == 1
    row = rows[0]
    assert row.market is Market.TPEx
    assert row.date == date(2026, 8, 3)
    assert row.code == "3306"
    assert row.yahoo == "3306.TWO"
    assert row.kind is CorporateActionKind.EX_DIVIDEND
    assert row.stock_dividend_ratio == Decimal("0.00000000")
    assert row.cash_dividend_per_share == Decimal("1.70000000")
    assert row.subscription_price_per_share == Decimal("0.00")
    assert row.source == "TPEx tpex_exright_prepost"


def test_filter_corporate_actions():
    rows = [
        *parse_twse_corporate_actions(TWSE_PAYLOAD),
        *parse_tpex_corporate_actions(TPEX_PAYLOAD),
    ]

    filtered = filter_corporate_actions(
        rows,
        market="TWSE",
        start=date(2026, 8, 20),
        kind="ex-rights",
    )

    assert [row.code for row in filtered] == ["4764"]


def test_filter_rejects_backwards_range():
    with pytest.raises(ValueError, match="end must be on or after start"):
        filter_corporate_actions([], start=date(2026, 8, 2), end=date(2026, 8, 1))


def test_find_corporate_actions_dispatches_market(monkeypatch):
    expected = parse_twse_corporate_actions(TWSE_PAYLOAD)

    def fake_fetch(market, *, timeout):
        assert market is Market.TWSE
        assert timeout == 3.0
        return expected

    monkeypatch.setattr(corporate_actions, "fetch_corporate_actions", fake_fetch)

    rows = corporate_actions.find_corporate_actions(
        "2496.TW",
        start=date(2026, 8, 1),
        end=date(2026, 8, 31),
        timeout=3.0,
    )
    assert [row.code for row in rows] == ["2496"]


def test_find_corporate_actions_requires_market_for_bare_symbol():
    with pytest.raises(ValueError, match="market is required"):
        corporate_actions.find_corporate_actions("2496")


def test_write_corporate_actions_csv(tmp_path):
    rows: list[CorporateAction] = parse_tpex_corporate_actions(TPEX_PAYLOAD)
    path = write_corporate_actions_csv(rows, tmp_path / "actions.csv")
    text = path.read_text(encoding="utf-8-sig")

    assert "cash_dividend_per_share" in text
    assert "3306.TWO" in text
    assert "ex-dividend" in text
