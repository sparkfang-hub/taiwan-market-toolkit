import json
import sys
from datetime import date
from decimal import Decimal

from taiwan_market_toolkit.cli import main
from taiwan_market_toolkit.directory import SecurityProfile
from taiwan_market_toolkit.history import HistoricalPrice
from taiwan_market_toolkit.quotes import ClosingQuote
from taiwan_market_toolkit.snapshots import SnapshotWriteResult
from taiwan_market_toolkit.symbols import Market
from taiwan_market_toolkit.valuation import ValuationMetrics


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


def test_company_cli_serializes_official_profile(monkeypatch, capsys):
    profile = SecurityProfile(
        market=Market.TWSE,
        code="2330",
        name="台灣積體電路製造股份有限公司",
        short_name="台積電",
        english_name="TSMC",
        industry="24",
        listing_date=date(1994, 9, 5),
    )

    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.find_company",
        lambda value, market, *, timeout: profile,
    )
    monkeypatch.setattr(sys, "argv", ["tw-market", "company", "2330.TW"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "2330"
    assert payload["market"] == "TWSE"
    assert payload["yahoo"] == "2330.TW"
    assert payload["short_name"] == "台積電"
    assert payload["listing_date"] == "1994-09-05"


def test_search_company_cli_filters_market(monkeypatch, capsys):
    profiles = [
        SecurityProfile(Market.TWSE, "2330", "台積電", "台積電", "TSMC", "24", None),
        SecurityProfile(Market.TPEx, "6488", "環球晶", "環球晶", "GlobalWafers", "24", None),
    ]
    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.fetch_company_directory",
        lambda *, timeout: profiles,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["tw-market", "search-company", "台積", "--market", "TWSE"],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    assert payload[0]["code"] == "2330"


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


def test_valuation_cli_serializes_official_metrics(monkeypatch, capsys):
    metrics = ValuationMetrics(
        market=Market.TWSE,
        date=date(2026, 8, 10),
        code="2330",
        name="台積電",
        pe_ratio=Decimal("25.50"),
        dividend_yield_pct=Decimal("1.75"),
        price_to_book=Decimal("6.80"),
    )
    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.find_valuation",
        lambda value, market, *, timeout: metrics,
    )
    monkeypatch.setattr(sys, "argv", ["tw-market", "valuation", "2330.TW"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "date": "2026-08-10",
        "code": "2330",
        "name": "台積電",
        "market": "TWSE",
        "pe_ratio": "25.50",
        "dividend_yield_pct": "1.75",
        "price_to_book": "6.80",
        "dividend_per_share": None,
    }


def test_history_cli_serializes_official_rows(monkeypatch, capsys):
    prices = [
        HistoricalPrice(
            market=Market.TWSE,
            code="2330",
            date=date(2026, 8, 11),
            open=Decimal("1000"),
            high=Decimal("1020"),
            low=Decimal("995"),
            close=Decimal("1010"),
            volume=1_234_000,
            trade_value=1_245_000_000,
            change=Decimal("10"),
            transactions=8_765,
            source="fixture",
        )
    ]

    def fake_fetch(value, market, *, start, end, timeout):
        assert value == "2330.TW"
        assert market is None
        assert start == date(2026, 8, 1)
        assert end == date(2026, 8, 11)
        assert timeout == 2.0
        return prices

    monkeypatch.setattr("taiwan_market_toolkit.cli.fetch_price_history", fake_fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tw-market",
            "history",
            "2330.TW",
            "--start",
            "2026-08-01",
            "--end",
            "2026-08-11",
            "--timeout",
            "2",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == 1
    assert payload["start"] == "2026-08-11"
    assert payload["data"][0]["close"] == "1010"
    assert payload["data"][0]["volume"] == 1_234_000


def test_history_cli_can_write_csv(tmp_path, monkeypatch, capsys):
    prices = [
        HistoricalPrice(
            Market.TWSE,
            "2330",
            date(2026, 8, 11),
            Decimal("1000"),
            Decimal("1020"),
            Decimal("995"),
            Decimal("1010"),
            1_234_000,
            1_245_000_000,
            Decimal("10"),
            8_765,
            "fixture",
        )
    ]
    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.fetch_price_history",
        lambda value, market, *, start, end, timeout: prices,
    )
    output = tmp_path / "history.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tw-market",
            "history",
            "2330.TW",
            "--start",
            "2026-08-01",
            "--end",
            "2026-08-11",
            "--output",
            str(output),
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == 1
    assert payload["path"] == str(output)
    assert output.exists()


def test_archive_quotes_cli_serializes_write_result(tmp_path, monkeypatch, capsys):
    snapshot_path = (
        tmp_path / "twse" / "closing_quotes" / "2026" / "2026-08-11.json"
    )

    def fake_archive(market, root, *, timeout, replace):
        assert market == "TWSE"
        assert root == str(tmp_path)
        assert timeout == 2.0
        assert replace is False
        return SnapshotWriteResult(
            source="twse/closing_quotes",
            date=date(2026, 8, 11),
            path=snapshot_path,
            sha256="abc123",
            bytes=321,
            created=True,
            replaced=False,
        )

    monkeypatch.setattr(
        "taiwan_market_toolkit.cli.archive_official_closing_snapshot",
        fake_archive,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tw-market",
            "archive-quotes",
            "--market",
            "TWSE",
            "--root",
            str(tmp_path),
            "--timeout",
            "2",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "source": "twse/closing_quotes",
        "date": "2026-08-11",
        "path": str(snapshot_path),
        "sha256": "abc123",
        "bytes": 321,
        "created": True,
        "replaced": False,
    }
