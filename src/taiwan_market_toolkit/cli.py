"""Command-line interface for taiwan-market-toolkit."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from typing import Any

from .analytics import (
    daily_returns,
    exponential_moving_average,
    simple_moving_average,
    summarize_ohlcv,
)
from .calendar import TaiwanTradingCalendar
from .corporate_actions import (
    CorporateAction,
    CorporateActionKind,
    fetch_corporate_actions,
    filter_corporate_actions,
    write_corporate_actions_csv,
)
from .directory import (
    SecurityProfile,
    fetch_company_directory,
    find_company,
    search_company_directory,
)
from .history import HistoricalPrice, fetch_price_history, write_history_csv
from .market_snapshot import (
    MarketSnapshotRow,
    fetch_market_snapshot,
    summarize_market_snapshot,
    write_market_snapshot_csv,
)
from .normalize import read_ohlcv_csv
from .overview import SecurityOverview, fetch_security_overview
from .quotes import ClosingQuote, fetch_closing_quote
from .snapshots import archive_official_closing_snapshot
from .symbols import normalize_market, normalize_symbol
from .validation import validate_ohlcv
from .valuation import ValuationMetrics, find_valuation

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

    valuation = subparsers.add_parser(
        "valuation",
        help="Fetch official P/E, dividend yield, and P/B metrics",
    )
    valuation.add_argument("value", help="Ticker such as 2330.TW or 6488.TWO")
    valuation.add_argument("--market", choices=_MARKET_CHOICES)
    valuation.add_argument("--timeout", type=float, default=10.0)

    overview = subparsers.add_parser(
        "overview",
        help="Fetch official company, closing quote, and valuation data together",
    )
    overview.add_argument("value", help="Ticker such as 2330.TW or 6488.TWO")
    overview.add_argument("--market", choices=_MARKET_CHOICES)
    overview.add_argument("--timeout", type=float, default=10.0)

    market_snapshot = subparsers.add_parser(
        "market-snapshot",
        help="Join the official listed-company, closing, and valuation snapshots",
    )
    market_snapshot.add_argument(
        "--market",
        choices=["TWSE", "TPEX"],
        help="Optional single market. Without it, both TWSE and TPEx are fetched.",
    )
    market_snapshot.add_argument("--timeout", type=float, default=10.0)
    market_snapshot.add_argument(
        "--output",
        help="Optional CSV path. Without it, joined rows are printed as JSON.",
    )
    market_snapshot.add_argument(
        "--summary-only",
        action="store_true",
        help="Print source coverage without embedding every joined row in JSON.",
    )

    history = subparsers.add_parser(
        "history",
        help="Fetch official monthly historical prices for a common equity",
    )
    history.add_argument("value", help="Four-digit common-equity ticker such as 2330.TW")
    history.add_argument("--market", choices=_MARKET_CHOICES)
    history.add_argument("--start", required=True, help="ISO start date, e.g. 2026-01-01")
    history.add_argument("--end", required=True, help="ISO end date, e.g. 2026-08-11")
    history.add_argument("--timeout", type=float, default=10.0)
    history.add_argument(
        "--cache-dir",
        help="Optional directory for exact monthly exchange-response caching.",
    )
    history.add_argument(
        "--refresh",
        action="store_true",
        help="Bypass completed-month cache entries and refresh them from the exchange.",
    )
    history.add_argument(
        "--output",
        help="Optional CSV path. Without this option, normalized rows are printed as JSON.",
    )

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

    corporate_actions = subparsers.add_parser(
        "corporate-actions",
        help="Fetch and export official ex-rights/ex-dividend announcements",
    )
    corporate_actions.add_argument("--market", choices=["TWSE", "TPEX"])
    corporate_actions.add_argument("--code", help="Optional security code filter")
    corporate_actions.add_argument("--start", help="Inclusive ISO date filter")
    corporate_actions.add_argument("--end", help="Inclusive ISO date filter")
    corporate_actions.add_argument(
        "--kind",
        choices=[item.value for item in CorporateActionKind],
        help="Optional normalized action kind filter",
    )
    corporate_actions.add_argument(
        "--output",
        help="Optional UTF-8 CSV path. Without it, print JSON.",
    )
    corporate_actions.add_argument("--timeout", type=float, default=10.0)

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


def _quote_payload(quote: ClosingQuote) -> dict[str, str | None]:
    return {
        "date": quote.date.isoformat(),
        "code": quote.code,
        "name": quote.name,
        "market": quote.market.value,
        "close": str(quote.close) if quote.close is not None else None,
    }


def _valuation_payload(metrics: ValuationMetrics) -> dict[str, str | None]:
    return {
        "date": metrics.date.isoformat(),
        "code": metrics.code,
        "name": metrics.name,
        "market": metrics.market.value,
        "pe_ratio": _json_value(metrics.pe_ratio),
        "dividend_yield_pct": _json_value(metrics.dividend_yield_pct),
        "price_to_book": _json_value(metrics.price_to_book),
        "dividend_per_share": _json_value(metrics.dividend_per_share),
    }


def _history_payload(item: HistoricalPrice) -> dict[str, Any]:
    return {
        "date": item.date.isoformat(),
        "market": item.market.value,
        "code": item.code,
        "open": _json_value(item.open),
        "high": _json_value(item.high),
        "low": _json_value(item.low),
        "close": _json_value(item.close),
        "volume": item.volume,
        "trade_value": item.trade_value,
        "change": _json_value(item.change),
        "transactions": item.transactions,
        "source": item.source,
    }


def _market_snapshot_payload(item: MarketSnapshotRow) -> dict[str, Any]:
    return {
        "market": item.market.value,
        "code": item.code,
        "yahoo": item.yahoo,
        "name": item.name,
        "short_name": item.short_name,
        "english_name": item.english_name,
        "industry": item.industry,
        "listing_date": _json_value(item.listing_date),
        "quote_date": _json_value(item.quote_date),
        "close": _json_value(item.close),
        "valuation_date": _json_value(item.valuation_date),
        "pe_ratio": _json_value(item.pe_ratio),
        "dividend_yield_pct": _json_value(item.dividend_yield_pct),
        "price_to_book": _json_value(item.price_to_book),
        "dividend_per_share": _json_value(item.dividend_per_share),
    }


def _market_snapshot_summary_payload(rows: list[MarketSnapshotRow]) -> dict[str, Any]:
    summary = summarize_market_snapshot(rows)
    return {
        "rows": summary.rows,
        "with_quote": summary.with_quote,
        "with_valuation": summary.with_valuation,
        "missing_quote": summary.missing_quote,
        "missing_valuation": summary.missing_valuation,
        "quote_dates": [value.isoformat() for value in summary.quote_dates],
        "valuation_dates": [value.isoformat() for value in summary.valuation_dates],
    }


def _overview_payload(overview: SecurityOverview) -> dict[str, Any]:
    return {
        "code": overview.code,
        "market": overview.market.value,
        "yahoo": overview.yahoo,
        "profile": _profile_payload(overview.profile),
        "quote": _quote_payload(overview.quote),
        "valuation": _valuation_payload(overview.valuation),
    }


def _corporate_action_payload(item: CorporateAction) -> dict[str, Any]:
    return {
        "date": item.date.isoformat(),
        "market": item.market.value,
        "code": item.code,
        "yahoo": item.yahoo,
        "name": item.name,
        "kind": item.kind.value,
        "raw_action": item.raw_action,
        "stock_dividend_ratio": _json_value(item.stock_dividend_ratio),
        "subscription_ratio": _json_value(item.subscription_ratio),
        "subscription_price_per_share": _json_value(item.subscription_price_per_share),
        "cash_dividend_per_share": _json_value(item.cash_dividend_per_share),
        "public_underwriting_shares": item.public_underwriting_shares,
        "employee_subscription_shares": item.employee_subscription_shares,
        "existing_shareholder_subscription_shares": item.existing_shareholder_subscription_shares,
        "existing_shareholder_subscription_per_thousand": _json_value(
            item.existing_shareholder_subscription_per_thousand
        ),
        "source": item.source,
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
        print(json.dumps(_quote_payload(result), ensure_ascii=False))
        return

    if args.command == "valuation":
        result = find_valuation(args.value, args.market, timeout=args.timeout)
        print(json.dumps(_valuation_payload(result), ensure_ascii=False))
        return

    if args.command == "overview":
        result = fetch_security_overview(args.value, args.market, timeout=args.timeout)
        print(json.dumps(_overview_payload(result), ensure_ascii=False))
        return

    if args.command == "market-snapshot":
        result = fetch_market_snapshot(args.market, timeout=args.timeout)
        summary = _market_snapshot_summary_payload(result)
        if args.output:
            destination = write_market_snapshot_csv(result, args.output)
            payload = {"path": str(destination), **summary}
        elif args.summary_only:
            payload = summary
        else:
            payload = {**summary, "data": [_market_snapshot_payload(item) for item in result]}
        print(json.dumps(payload, ensure_ascii=False))
        return

    if args.command == "history":
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
        cache_options: dict[str, Any] = {}
        if args.cache_dir:
            cache_options["cache_dir"] = args.cache_dir
        if args.refresh:
            cache_options["refresh"] = True
        result = fetch_price_history(
            args.value,
            args.market,
            start=start,
            end=end,
            timeout=args.timeout,
            **cache_options,
        )
        if args.output:
            destination = write_history_csv(result, args.output)
            payload = {
                "path": str(destination),
                "rows": len(result),
                "start": result[0].date.isoformat() if result else None,
                "end": result[-1].date.isoformat() if result else None,
            }
        else:
            payload = {
                "rows": len(result),
                "start": result[0].date.isoformat() if result else None,
                "end": result[-1].date.isoformat() if result else None,
                "data": [_history_payload(item) for item in result],
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

    if args.command == "corporate-actions":
        start = date.fromisoformat(args.start) if args.start else None
        end = date.fromisoformat(args.end) if args.end else None
        rows = fetch_corporate_actions(args.market, timeout=args.timeout)
        rows = filter_corporate_actions(
            rows,
            code=args.code,
            start=start,
            end=end,
            kind=args.kind,
        )
        if args.output:
            destination = write_corporate_actions_csv(rows, args.output)
            payload = {"path": str(destination), "rows": len(rows)}
        else:
            payload = {
                "rows": len(rows),
                "data": [_corporate_action_payload(item) for item in rows],
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
