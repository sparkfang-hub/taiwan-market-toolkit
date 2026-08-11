"""Smoke-check official Taiwan exchange sources used by the toolkit.

This script is intended for scheduled/manual GitHub Actions runs. Unit tests remain
fixture-based and do not depend on live network availability.
"""

from datetime import date

from taiwan_market_toolkit import (
    fetch_tpex_closing_quotes,
    fetch_tpex_company_directory,
    fetch_tpex_history_month,
    fetch_tpex_valuation,
    fetch_twse_closing_quotes,
    fetch_twse_company_directory,
    fetch_twse_history_month,
    fetch_twse_holiday_schedule,
    fetch_twse_valuation,
)
from taiwan_market_toolkit.corporate_actions import (
    fetch_tpex_corporate_actions,
    fetch_twse_corporate_actions,
)


def _previous_month(today: date) -> date:
    if today.month == 1:
        return date(today.year - 1, 12, 1)
    return date(today.year, today.month - 1, 1)


def main() -> None:
    twse_quotes = fetch_twse_closing_quotes(timeout=20.0)
    tpex_quotes = fetch_tpex_closing_quotes(timeout=20.0)
    twse_companies = fetch_twse_company_directory(timeout=20.0)
    tpex_companies = fetch_tpex_company_directory(timeout=20.0)
    twse_valuation = fetch_twse_valuation(timeout=20.0)
    tpex_valuation = fetch_tpex_valuation(timeout=20.0)
    twse_holidays = fetch_twse_holiday_schedule(timeout=20.0)
    twse_actions = fetch_twse_corporate_actions(timeout=20.0)
    tpex_actions = fetch_tpex_corporate_actions(timeout=20.0)

    history_month = _previous_month(date.today())
    twse_history = fetch_twse_history_month("2330", history_month, timeout=20.0)
    tpex_history = fetch_tpex_history_month("6488", history_month, timeout=20.0)

    if not twse_quotes:
        raise RuntimeError("TWSE closing quote source returned no rows")
    if not tpex_quotes:
        raise RuntimeError("TPEx closing quote source returned no rows")
    if not twse_companies:
        raise RuntimeError("TWSE company directory source returned no rows")
    if not tpex_companies:
        raise RuntimeError("TPEx company directory source returned no rows")
    if not twse_valuation:
        raise RuntimeError("TWSE valuation source returned no rows")
    if not tpex_valuation:
        raise RuntimeError("TPEx valuation source returned no rows")
    if not twse_holidays:
        raise RuntimeError("TWSE holiday source returned no rows")
    if not twse_actions:
        raise RuntimeError("TWSE corporate-action source returned no rows")
    if not tpex_actions:
        raise RuntimeError("TPEx corporate-action source returned no rows")
    if not twse_history:
        raise RuntimeError(f"TWSE historical source returned no rows for {history_month:%Y-%m}")
    if not tpex_history:
        raise RuntimeError(f"TPEx historical source returned no rows for {history_month:%Y-%m}")

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
    print("TWSE valuation:", len(twse_valuation), "rows")
    print("TPEx valuation:", len(tpex_valuation), "rows")
    print("TWSE holiday schedule:", len(twse_holidays), "rows")
    print("TWSE corporate actions:", len(twse_actions), "rows")
    print("TPEx corporate actions:", len(tpex_actions), "rows")
    print("TWSE history:", len(twse_history), "rows for", history_month.strftime("%Y-%m"))
    print("TPEx history:", len(tpex_history), "rows for", history_month.strftime("%Y-%m"))


if __name__ == "__main__":
    main()
