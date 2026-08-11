"""Smoke-check official Taiwan exchange sources used by the toolkit.

This script is intended for scheduled/manual GitHub Actions runs. Unit tests remain
fixture-based and do not depend on live network availability.
"""

from taiwan_market_toolkit import (
    fetch_tpex_closing_quotes,
    fetch_twse_closing_quotes,
    fetch_twse_holiday_schedule,
)


def main() -> None:
    twse_quotes = fetch_twse_closing_quotes(timeout=20.0)
    tpex_quotes = fetch_tpex_closing_quotes(timeout=20.0)
    twse_holidays = fetch_twse_holiday_schedule(timeout=20.0)

    if not twse_quotes:
        raise RuntimeError("TWSE closing quote source returned no rows")
    if not tpex_quotes:
        raise RuntimeError("TPEx closing quote source returned no rows")
    if not twse_holidays:
        raise RuntimeError("TWSE holiday source returned no rows")

    print(
        "TWSE quotes:",
        len(twse_quotes),
        "rows, snapshot date",
        max(quote.date for quote in twse_quotes).isoformat(),
    )
    print(
        "TPEx quotes:",
        len(tpex_quotes),
        "rows, snapshot date",
        max(quote.date for quote in tpex_quotes).isoformat(),
    )
    print("TWSE holiday schedule:", len(twse_holidays), "rows")


if __name__ == "__main__":
    main()
