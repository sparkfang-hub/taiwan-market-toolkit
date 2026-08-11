"""Fetch current official ex-rights/ex-dividend announcements."""

from taiwan_market_toolkit import fetch_corporate_actions

rows = fetch_corporate_actions()

print(f"rows={len(rows)}")
for row in rows[:10]:
    print(
        row.date.isoformat(),
        row.market.value,
        row.code,
        row.name,
        row.kind.value,
        row.cash_dividend_per_share,
        row.stock_dividend_ratio,
    )
