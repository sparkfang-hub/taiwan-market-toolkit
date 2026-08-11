"""Command-line interface for taiwan-market-toolkit."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal

from .analytics import (
    daily_returns,
    exponential_moving_average,
    simple_moving_average,
    summarize_ohlcv,
)
from .calendar import TaiwanTradingCalendar
from .directory import (
    SecurityProfile,
    fetch_company_directory,
    find_company,
    search_company_directory,
)
from .normalize import read_ohlcv_csv
from .quotes import fetch_closing_quote
from .snapshots import archive_official_closing_snapshot
from .symbols import normalize_market, normalize_symbol
from .validation import validate_ohlcv

_MARKET_CHOICES = ["TWSE", "TPEX", "TW", "TWO", "OTC"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tw-market",
        description="Taiwan market utilities",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    symbol = subparsers.add_parser("symbol", help="Normalize a Taiwan stock ticker")
    symbol.add_argument("value")
    symbol.add_argument("--market", choices=_MARKET_CHOICES)

    company = subparsers.add_parser(
        "company",
        help="Fetch one official TWSE/TPEx company profile",
    )
    company.add_argument("value", help="Ticker such as 2330.TW or 6488.TWO")
    company.add_argument("--market", choices=_MARKET_CHOICES)
    company.add_argument("--timeout", type=float, default=10.0)

    company_search = subparsers.add_parser(
        "search-company",
        help="Search the official TWSE/TPEx company directory",
    )
    company_search.add_argument("query")
    company_search.add_argument("--market", choices=["TWSE", "TPEX"])
    company_search.add_argument("--limit", type=int, default=20)
    company_search.add_argument("--timeout", type=float, default=10.0)

    quote = subparsers.add_parser(
        "quote",
        help="Fetch the latest official closing quote for a Taiwan security",
    )
    quote.add_argument("value", help="Ticker such as 2330.TW or 6488.TWO")
    quote.add_argument("--market", choices=_MARKET_CHOICES)
    quote.add_argument("--timeout", type=float, default=10.0)

    archive = subparsers.add_parser(
        "archive-quotes",
        help="Fetch and preserve an exact official closing snapshot locally",
    )
    archive.add_argument("--market", required=True, choices=_MARKET_CHOICES)
    archive.add_argument("--root", default="market-data", help="Local archive root directory")
    archive.add_argument("--timeout", type=float, default=10.0)
    archive.add_argument(
        "--replace",
        action="store_true",
        help="Explicitly replace different bytes already stored for the same market/date",
    )

    calendar = subparsers.add_parser("calendar", help="Query the lightweight trading calendar")
    calendar.add_argument("day", help="ISO date, e.g. 2026-08-11")
    calendar.add_argument("--next", action="store_true", dest="next_day")
    calendar.add_argument("--previous", action="store_true", dest="previous_day")

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

    analyze = subparsers.add_parser(
        "analyze",
        help="Summarize an OHLCV CSV and optionally calculate moving averages",
    )
    analyze.add_argument("path")
    analyze.add_argument(
        "--sma",
        type=int,
        action="append",
        default=[],
        metavar="WINDOW",
        help="Calculate the latest simple moving average for a window; repeatable",
    )
    analyze.add_argument(
        "--ema",
        type=int,
        action="append",
        default=[],
        metavar="WINDOW",
        help="Calculate the latest exponential moving average for a window; repeatable",
    )

    return parser


def _json_value(value: Decimal | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _profile_payload(profile: SecurityProfile) -> dict[str, str | None]:
    return {
        "code": profile.code,
        "market": profile.market.value,
        "yahoo": profile.yahoo,
        "name": profile.name,
        "short_name": profile.short_name,
        "english_name": profile.english_name,
        "industry": profile.industry,
        "listing_date": profile.listing_date.isoformat() if profile.listing_date else None,
    }


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

    if args.command == "company":
        result = find_company(args.value, args.market, timeout=args.timeout)
        print(json.dumps(_profile_payload(result), ensure_ascii=False))
        return

    if args.command == "search-company":
        profiles = fetch_company_directory(timeout=args.timeout)
        market = normalize_market(args.market) if args.market else None
        matches = search_company_directory(
            profiles,
            args.query,
            market=market,
            limit=args.limit,
        )
        print(json.dumps([_profile_payload(item) for item in matches], ensure_ascii=False))
        return

    if args.command == "quote":
        result = fetch_closing_quote(args.value, args.market, timeout=args.timeout)
        payload = {
            "date": result.date.isoformat(),
            "code": result.code,
            "name": result.name,
            "market": result.market.value,
            "close": str(result.close) if result.close is not None else None,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return

    if args.command == "archive-quotes":
        result = archive_official_closing_snapshot(
            args.market,
            args.root,
            timeout=args.timeout,
            replace=args.replace,
        )
        payload = {
            "source": result.source,
            "date": result.date.isoformat(),
            "path": str(result.path),
            "sha256": result.sha256,
            "bytes": result.bytes,
            "created": result.created,
            "replaced": result.replaced,
        }
        print(json.dumps(payload, ensure_ascii=False))
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

    if args.command == "analyze":
        rows = read_ohlcv_csv(args.path)
        summary = summarize_ohlcv(rows)
        returns = daily_returns(rows)
        payload = {
            "rows": summary.rows,
            "start": _json_value(summary.start),
            "end": _json_value(summary.end),
            "min_close": _json_value(summary.min_close),
            "max_close": _json_value(summary.max_close),
            "total_volume": summary.total_volume,
            "latest_return": _json_value(returns[-1].value) if returns else None,
            "sma": {},
            "ema": {},
        }
        for window in args.sma:
            points = simple_moving_average(rows, window)
            payload["sma"][str(window)] = _json_value(points[-1].value) if points else None
        for window in args.ema:
            points = exponential_moving_average(rows, window)
            payload["ema"][str(window)] = _json_value(points[-1].value) if points else None
        print(json.dumps(payload, ensure_ascii=False))
        return

    parser.error("unknown command")
