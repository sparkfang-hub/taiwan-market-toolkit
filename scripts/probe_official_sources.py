"""Smoke-check official Taiwan exchange sources used by the toolkit.

This script is intended for scheduled/manual GitHub Actions runs. Unit tests remain
fixture-based and do not depend on live network availability.
"""

from taiwan_market_toolkit import (
    fetch_tpex_closing_quotes,
    fetch_tpex_company_directory,
    fetch_twse_closing_quotes,
    fetch_twse_company_directory,
    fetch_twse_holiday_schedule,
)


def main() -> None:
    twse_quotes = fetch_twse_closing_quotes(timeout=20.0)
    tpex_quotes = fetch_tpex_closing_quotes(timeout=20.0)
    twse_companies = fetch_twse_company_directory(timeout=20.0)
    tpex_companies = fetch_tpex_company_directory(timeout=20.0)
    twse_holidays = fetch_twse_holiday_schedule(timeout=20.0)

    if not twse_quotes:
        raise RuntimeError("TWSE closing quote source returned no rows")
    if not tpex_quotes:
        raise RuntimeError("TPEx closing quote source returned no rows")
    if not twse_companies:
        raise RuntimeError("TWSE company directory source returned no rows")
    if not tpex_companies:
        raise RuntimeError("TPEx company directory source returned no rows")
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
    print("TWSE company directory:", len(twse_companies), "rows")
    print("TPEx company directory:", len(tpex_companies), "rows")
    print("TWSE holiday schedule:", len(twse_holidays), "rows")


if __name__ == "__main__":
    main()
