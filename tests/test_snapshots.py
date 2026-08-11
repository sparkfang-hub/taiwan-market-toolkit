from datetime import date

import pytest

from taiwan_market_toolkit.snapshots import (
    SnapshotStore,
    archive_official_closing_snapshot,
)


TWSE_PAYLOAD = b"""[
  {"Date":"20260811","Code":"2330","Name":"TSMC","ClosingPrice":"1005"}
]"""

TPEX_PAYLOAD = b"""[
  {"Date":"115/08/11","SecuritiesCompanyCode":"6488","CompanyName":"GlobalWafers","Close":"350.5"}
]"""


def test_snapshot_store_preserves_exact_bytes_and_is_idempotent(tmp_path):
    store = SnapshotStore(tmp_path)
    day = date(2026, 8, 11)

    first = store.put("twse/closing_quotes", day, TWSE_PAYLOAD)
    second = store.put("twse/closing_quotes", day, TWSE_PAYLOAD)

    assert first.created is True
    assert first.replaced is False
    assert second.created is False
    assert second.replaced is False
    assert store.read("twse/closing_quotes", day) == TWSE_PAYLOAD
    assert first.path == tmp_path / "twse" / "closing_quotes" / "2026" / "2026-08-11.json"


def test_snapshot_store_refuses_silent_same_day_replacement(tmp_path):
    store = SnapshotStore(tmp_path)
    day = date(2026, 8, 11)
    store.put("twse/closing_quotes", day, TWSE_PAYLOAD)

    with pytest.raises(FileExistsError, match="different content"):
        store.put("twse/closing_quotes", day, b"[]")

    replaced = store.put("twse/closing_quotes", day, b"[]", replace=True)
    assert replaced.created is False
    assert replaced.replaced is True
    assert store.read("twse/closing_quotes", day) == b"[]"


def test_snapshot_store_lists_dates_and_latest(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("tpex/closing_quotes", date(2026, 8, 10), b"[]")
    store.put("tpex/closing_quotes", date(2026, 8, 11), TPEX_PAYLOAD)

    assert store.dates("tpex/closing_quotes") == [date(2026, 8, 10), date(2026, 8, 11)]
    latest = store.latest("tpex/closing_quotes")
    assert latest == (date(2026, 8, 11), TPEX_PAYLOAD)


def test_snapshot_store_rejects_path_traversal(tmp_path):
    store = SnapshotStore(tmp_path)

    with pytest.raises(ValueError, match="unsafe snapshot source"):
        store.path_for("../outside", date(2026, 8, 11))


def test_snapshot_store_requires_valid_json(tmp_path):
    store = SnapshotStore(tmp_path)

    with pytest.raises(ValueError, match="valid UTF-8 JSON"):
        store.put("twse/closing_quotes", date(2026, 8, 11), b"not-json")


def test_archive_official_twse_snapshot_uses_payload_date(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taiwan_market_toolkit.snapshots.fetch_twse_closing_payload",
        lambda *, timeout: TWSE_PAYLOAD,
    )

    result = archive_official_closing_snapshot("TWSE", tmp_path, timeout=1)

    assert result.date == date(2026, 8, 11)
    assert result.source == "twse/closing_quotes"
    assert result.path.read_bytes() == TWSE_PAYLOAD


def test_archive_official_tpex_snapshot_uses_payload_date(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taiwan_market_toolkit.snapshots.fetch_tpex_closing_payload",
        lambda *, timeout: TPEX_PAYLOAD,
    )

    result = archive_official_closing_snapshot("TPEX", tmp_path, timeout=1)

    assert result.date == date(2026, 8, 11)
    assert result.source == "tpex/closing_quotes"
    assert result.path.read_bytes() == TPEX_PAYLOAD
