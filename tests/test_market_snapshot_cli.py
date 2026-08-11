import json
import sys
from datetime import date
from decimal import Decimal

from taiwan_market_toolkit.cli import main
from taiwan_market_toolkit.market_snapshot import MarketSnapshotRow
from taiwan_market_toolkit.symbols import Market


def _row() -> MarketSnapshotRow:
    return MarketSnapshotRow(
        market=Market.TWSE,
        code="2330",
        name="台灣積體電路製造股份有限公司",
        short_name="台積電",
        english_name="TSMC",
        industry="24",
        listing_date=date(1994, 9, 5),
        quote_date=date(2026, 8, 11),
        close=Decimal("1005"),
        valuation_date=date(2026, 8, 10),
        pe_ratio=Decimal("25.5"),
        dividend_yield_pct=Decimal("1.75"),
        price_to_book=Decimal("6.8"),
        dividend_per_share=None,
    )


def test_market_snapshot_cli_summary_only(monkeypatch, capsys):
    def fake_fetch(market, *, timeout):
        assert market == "TWSE"
        assert timeout == 3.0
        return [_row()]

    monkeypatch.setattr("taiwan_market_toolkit.cli.fetch_market_snapshot", fake_fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tw-market",
            "market-snapshot",
            "--market",
            "TWSE",
            "--timeout",
            "3",
            "--summary-only",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "rows": 1,
        "with_quote": 1,
        "with_valuation": 1,
        "missing_quote": 0,
        "missing_valuation": 0,
        "quote_dates": ["2026-08-11"],
        "valuation_dates": ["2026-08-10"],
    }


def test_market_snapshot_cli_embeds_joined_rows(monkeypatch, capsys):
    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.fetch_market_snapshot",
        lambda market, *, timeout: [_row()],
    )
    monkeypatch.setattr(sys, "argv", ["tw-market", "market-snapshot"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == 1
    assert payload["data"][0]["code"] == "2330"
    assert payload["data"][0]["yahoo"] == "2330.TW"
    assert payload["data"][0]["close"] == "1005"
    assert payload["data"][0]["valuation_date"] == "2026-08-10"
