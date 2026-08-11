"""Command-line interface for taiwan-market-toolkit."""

from __future__ import annotations

import argparse
import json
from datetime import date

from .calendar import TaiwanTradingCalendar
from .normalize import read_ohlcv_csv
from .symbols import normalize_symbol
from .validation import validate_ohlcv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tw-market",
        description="Taiwan market utilities",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    symbol = subparsers.add_parser(
        "symbol",
        help="Normalize a Taiwan stock ticker",
    )
    symbol.add_argument("value")
    symbol.add_argument(
        "--market",
        choices=["TWSE", "TPEX", "TW", "TWO", "OTC"],
    )

    calendar = subparsers.add_parser(
        "calendar",
        help="Query the lightweight trading calendar",
    )
    calendar.add_argument("day", help="ISO date, e.g. 2026-08-11")
    calendar.add_argument("--next", action="store_true", dest="next_day")
    calendar.add_argument(
        "--previous",
        action="store_true",
        dest="previous_day",
    )

    validate = subparsers.add_parser(
        "validate",
        help="Normalize and validate an OHLCV CSV file",
    )
    validate.add_argument("path")
    validate.add_argument(
        "--no-sort",
        action="store_true",
        help="Preserve CSV row order so out-of-order rows are reported",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "symbol":
        result = normalize_symbol(args.value, args.market)
        payload = {
            "code": result.code,
            "market": result.market.value if result.market else None,
            "yahoo": result.yahoo,
        }
        print(json.dumps(payload))
        return

    if args.command == "calendar":
        target = date.fromisoformat(args.day)
        calendar = TaiwanTradingCalendar()
        if args.next_day:
            print(calendar.next_trading_day(target).isoformat())
        elif args.previous_day:
            print(calendar.previous_trading_day(target).isoformat())
        else:
            print("open" if calendar.is_trading_day(target) else "closed")
        return

    if args.command == "validate":
        rows = read_ohlcv_csv(args.path, sort=not args.no_sort)
        issues = validate_ohlcv(rows)
        payload = {
            "rows": len(rows),
            "valid": not issues,
            "issues": [
                {"row": issue.row, "code": issue.code, "message": issue.message}
                for issue in issues
            ],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return

    parser.error("unknown command")
