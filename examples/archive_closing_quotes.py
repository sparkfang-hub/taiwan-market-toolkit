"""Archive exact official TWSE and TPEx closing snapshots locally."""

from taiwan_market_toolkit import archive_official_closing_snapshot

for market in ("TWSE", "TPEX"):
    result = archive_official_closing_snapshot(market, "market-data")
    print(
        market,
        result.date.isoformat(),
        result.path,
        result.sha256,
        "created" if result.created else "unchanged",
    )
