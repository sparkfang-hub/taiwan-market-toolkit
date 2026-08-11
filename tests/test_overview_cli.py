import json
import sys
from datetime import date
from decimal import Decimal

from taiwan_market_toolkit import (
    ClosingQuote,
    Market,
    SecurityOverview,
    SecurityProfile,
    ValuationMetrics,
)
from taiwan_market_toolkit.cli import main


def test_overview_cli_preserves_independent_source_dates(monkeypatch, capsys):
    overview = SecurityOverview(
        profile=SecurityProfile(
            market=Market.TWSE,
            code="2330",
            name="台灣積體電路製造股份有限公司",
            short_name="台積電",
            english_name="TSMC",
            industry="24",
            listing_date=date(1994, 9, 5),
        ),
        quote=ClosingQuote(
            market=Market.TWSE,
            date=date(2026, 8, 11),
            code="2330",
            name="台積電",
            close=Decimal("1005"),
        ),
        valuation=ValuationMetrics(
            market=Market.TWSE,
            date=date(2026, 8, 10),
            code="2330",
            name="台積電",
            pe_ratio=Decimal("25.50"),
            dividend_yield_pct=Decimal("1.75"),
            price_to_book=Decimal("6.80"),
        ),
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.fetch_security_overview",
        lambda value, market, *, timeout: overview,
    )
    monkeypatch.setattr(sys, "argv", ["tw-market", "overview", "2330.TW"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "2330"
    assert payload["market"] == "TWSE"
    assert payload["yahoo"] == "2330.TW"
    assert payload["profile"]["short_name"] == "台積電"
    assert payload["quote"]["date"] == "2026-08-11"
    assert payload["quote"]["close"] == "1005"
    assert payload["valuation"]["date"] == "2026-08-10"
    assert payload["valuation"]["pe_ratio"] == "25.50"
