from datetime import date

import pytest

from taiwan_market_toolkit import history
from taiwan_market_toolkit.history_cache import HistoricalPayloadCache
from taiwan_market_toolkit.symbols import Market

PAST_TWSE_PAYLOAD = b'''{
  "stat": "OK",
  "data": [
    ["114/07/01", "1,000", "1,010,000", "1000", "1020", "995", "1010", "+10", "100"]
  ]
}'''


def test_history_cache_preserves_exact_bytes_and_digest(tmp_path):
    cache = HistoricalPayloadCache(tmp_path)
    month = date(2025, 7, 1)

    result = cache.write(Market.TWSE, "2330", month, PAST_TWSE_PAYLOAD)

    assert result.created is True
    assert result.replaced is False
    assert cache.read(Market.TWSE, "2330", month) == PAST_TWSE_PAYLOAD
    assert result.path == tmp_path / "twse" / "2330" / "2025" / "2025-07.json"
    assert cache.digest_path_for(Market.TWSE, "2330", month).exists()


def test_history_cache_identical_write_is_idempotent(tmp_path):
    cache = HistoricalPayloadCache(tmp_path)
    month = date(2025, 7, 1)

    first = cache.write("TWSE", "2330", month, PAST_TWSE_PAYLOAD)
    second = cache.write("TWSE", "2330", month, PAST_TWSE_PAYLOAD)

    assert first.sha256 == second.sha256
    assert second.created is False
    assert second.replaced is False


def test_history_cache_refuses_changed_payload_without_replace(tmp_path):
    cache = HistoricalPayloadCache(tmp_path)
    month = date(2025, 7, 1)
    cache.write("TWSE", "2330", month, PAST_TWSE_PAYLOAD)

    with pytest.raises(FileExistsError, match="different historical payload"):
        cache.write("TWSE", "2330", month, b'{"stat":"OK","data":[]}')

    replaced = cache.write(
        "TWSE",
        "2330",
        month,
        b'{"stat":"OK","data":[]}',
        replace=True,
    )
    assert replaced.replaced is True


def test_history_cache_detects_digest_corruption(tmp_path):
    cache = HistoricalPayloadCache(tmp_path)
    month = date(2025, 7, 1)
    result = cache.write("TWSE", "2330", month, PAST_TWSE_PAYLOAD)
    result.path.write_bytes(b'{"stat":"OK","data":[]}')

    with pytest.raises(ValueError, match="SHA-256"):
        cache.read("TWSE", "2330", month)


def test_history_cache_rejects_unsafe_code(tmp_path):
    cache = HistoricalPayloadCache(tmp_path)

    with pytest.raises(ValueError, match="unsafe security code"):
        cache.path_for("TWSE", "../2330", date(2025, 7, 1))


def test_fetch_price_history_reuses_completed_cached_month(tmp_path, monkeypatch):
    calls = []

    def fake_payload(code, month, *, timeout):
        calls.append((code, month, timeout))
        return PAST_TWSE_PAYLOAD

    monkeypatch.setattr("taiwan_market_toolkit.history.fetch_twse_history_payload", fake_payload)

    first = history.fetch_price_history(
        "2330.TW",
        start=date(2025, 7, 1),
        end=date(2025, 7, 31),
        cache_dir=tmp_path,
        request_interval=0,
    )
    second = history.fetch_price_history(
        "2330.TW",
        start=date(2025, 7, 1),
        end=date(2025, 7, 31),
        cache_dir=tmp_path,
        request_interval=0,
    )

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].close == second[0].close
    assert len(calls) == 1


def test_fetch_price_history_refresh_bypasses_completed_cache(tmp_path, monkeypatch):
    calls = []

    def fake_payload(code, month, *, timeout):
        calls.append((code, month, timeout))
        return PAST_TWSE_PAYLOAD

    monkeypatch.setattr("taiwan_market_toolkit.history.fetch_twse_history_payload", fake_payload)

    history.fetch_price_history(
        "2330.TW",
        start=date(2025, 7, 1),
        end=date(2025, 7, 31),
        cache_dir=tmp_path,
        request_interval=0,
    )
    history.fetch_price_history(
        "2330.TW",
        start=date(2025, 7, 1),
        end=date(2025, 7, 31),
        cache_dir=tmp_path,
        refresh=True,
        request_interval=0,
    )

    assert len(calls) == 2
