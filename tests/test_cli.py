import json
import sys
from datetime import date
from decimal import Decimal

from taiwan_market_toolkit.cli import main
from taiwan_market_toolkit.quotes import ClosingQuote
from taiwan_market_toolkit.symbols import Market


def test_analyze_cli_reports_summary_and_moving_averages(tmp_path, monkeypatch, capsys):
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text(
        """date,open,high,low,close,volume
2026-08-10,100,100,100,100,10
2026-08-11,110,110,110,110,20
2026-08-12,121,121,121,121,30
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["tw-market", "analyze", str(csv_path), "--sma", "2", "--ema", "2"],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == 3
    assert payload["start"] == "2026-08-10"
    assert payload["end"] == "2026-08-12"
    assert payload["min_close"] == "100"
    assert payload["max_close"] == "121"
    assert payload["total_volume"] == 60
    assert payload["latest_return"] == "0.1"
    assert payload["sma"]["2"] == "115.5"
    assert payload["ema"]["2"] == "115.6666666666666666666666667"


def test_quote_cli_serializes_official_quote(monkeypatch, capsys):
    def fake_fetch(value, market, *, timeout):
        assert value == "2330.TW"
        assert market is None
        assert timeout == 3.0
        return ClosingQuote(
            market=Market.TWSE,
            date=date(2026, 8, 11),
            code="2330",
            name="台積電",
            close=Decimal("1005"),
        )

    monkeypatch.setattr("taiwan_market_toolkit.cli.fetch_closing_quote", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["tw-market", "quote", "2330.TW", "--timeout", "3"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "date": "2026-08-11",
        "code": "2330",
        "name": "台積電",
        "market": "TWSE",
        "close": "1005",
    }
