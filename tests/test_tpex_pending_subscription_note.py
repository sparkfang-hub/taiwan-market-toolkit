from taiwan_market_toolkit.corporate_actions import parse_tpex_corporate_actions


def test_tpex_note_4_marks_pending_subscription_price():
    payload = """[
      {
        "ExRrightsExDividendDate": "1150818",
        "SecuritiesCompanyCode": "1234",
        "CompanyName": "測試",
        "ExRrightsExDividend": "除權",
        "StockDividendRatio": "0",
        "SubscriptionRatioToNewSharesIssued": "0.1",
        "SubscriptionPricePerShare": "註4",
        "CashDividend": "0",
        "AllocatedForPublicUnderwriting": "0",
        "SubscribedByEmployees": "0",
        "SubscribedByExistingShareholders": "0",
        "SubscribedProRataInThousandShares": "0"
      }
    ]"""

    row = parse_tpex_corporate_actions(payload)[0]

    assert row.subscription_price_per_share is None
