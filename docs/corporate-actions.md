# Corporate actions

Taiwan Market Toolkit can normalize current ex-rights and ex-dividend announcement tables from both official exchanges.

Supported announcement sources:

- TWSE `exchangeReport/TWT48U_ALL`
- TPEx `tpex_exright_prepost`

These are preview/announcement feeds. They are useful inputs for research and future adjusted-price work, but they are not themselves an adjusted-price series.

## Python

```python
from taiwan_market_toolkit.corporate_actions import fetch_corporate_actions

rows = fetch_corporate_actions()
for row in rows[:5]:
    print(
        row.date,
        row.market.value,
        row.code,
        row.kind.value,
        row.cash_dividend_per_share,
        row.stock_dividend_ratio,
    )
```

Fetch one exchange only:

```python
rows = fetch_corporate_actions("TWSE")
```

## CLI

The CLI prints normalized JSON by default and writes UTF-8 CSV when --output is supplied:

```bash
tw-market corporate-actions --market TWSE --code 2330 --start 2026-01-01 --output market-data/corporate-actions.csv
```

Find current announcements for one security:

```python
from datetime import date
from taiwan_market_toolkit.corporate_actions import find_corporate_actions

rows = find_corporate_actions(
    "2330.TW",
    start=date(2026, 1, 1),
    end=date(2026, 12, 31),
)
```

## Common model

`CorporateAction` preserves the fields that have clear meaning across both announcement sources:

- exchange and security code;
- ex-rights/ex-dividend date;
- security name;
- normalized action kind plus the original exchange label;
- stock-dividend ratio;
- cash-capital-increase subscription ratio;
- subscription price per share;
- cash dividend per share;
- public-underwriting, employee-subscription, and existing-shareholder share counts where published;
- existing-shareholder subscription amount per thousand shares where published;
- explicit source identifier.

The toolkit maps TWSE labels such as `權`, `息`, and `權息` and TPEx labels such as `除權`, `除息`, and `除權息` into a common enum. The original label is retained in `raw_action`.

## Missing and pending values

An empty exchange field or a value such as `尚未公告` remains `None`. A published numeric zero remains numeric zero. This distinction is important for capital increases and dividend announcements because "not announced yet" is not equivalent to zero.

The parser does not infer a subscription price or dividend amount from other fields.

## CSV export

```python
from taiwan_market_toolkit.corporate_actions import (
    fetch_corporate_actions,
    write_corporate_actions_csv,
)

rows = fetch_corporate_actions()
write_corporate_actions_csv(rows, "market-data/corporate-actions.csv")
```

## Adjusted prices are a separate layer

This module deliberately stops at normalized official announcement inputs. Building an adjusted historical price series requires an explicit methodology covering at least:

- cash dividends;
- stock dividends;
- cash capital increases and subscription terms;
- capital reductions;
- stock splits or consolidations;
- how reference prices and historical observations are transformed;
- whether the series is price-return or total-return oriented.

Those choices should be documented and tested rather than guessed from price jumps. A future adjustment layer can consume `CorporateAction` together with official calculation-result feeds while keeping the original unadjusted history intact.

## Source monitoring

Normal tests use fixtures. The scheduled official-source smoke workflow also fetches both corporate-action announcement endpoints so upstream schema drift or source outages are visible without making every pull request depend on exchange uptime.
