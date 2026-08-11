# Examples

These examples are intentionally small and runnable from a development checkout.

## Traditional Chinese OHLCV CSV

The toolkit recognizes common Traditional Chinese headers and ROC-calendar dates:

```bash
python examples/validate_chinese_csv.py
```

The accompanying `sample_ohlcv_zh.csv` uses headers such as `交易日期`, `開盤價`, `收盤價`, and `成交股數`, with dates such as `115/08/11`.

The same file can be checked through the CLI:

```bash
tw-market validate examples/sample_ohlcv_zh.csv
```

## Official TWSE trading calendar

This example performs a read-only request to the official TWSE OpenAPI holiday schedule:

```bash
python examples/check_twse_calendar.py
```

For reproducible research, applications should cache the exact official payload used for a run rather than assuming a future response will remain unchanged.

## Official historical prices

This example fetches one month of official TWSE common-equity history, converts it to the canonical OHLCV model, and calculates SMA5:

```bash
python examples/fetch_history.py
```

The equivalent CLI workflow can print JSON or write normalized CSV:

```bash
tw-market history 2330.TW --start 2026-07-01 --end 2026-07-31
tw-market history 2330.TW --start 2026-07-01 --end 2026-07-31 --output data/2330.csv
```

Historical fetching is monthly, paced, and bounded. The v0.1 adapter intentionally supports ordinary four-digit common equities only so TPEx trading-lot units are not incorrectly applied to ETFs or other products.

## Archive official closing snapshots

This example fetches the current official TWSE and TPEx closing snapshots and stores their exact JSON response bytes under a local `market-data/` directory:

```bash
python examples/archive_closing_quotes.py
```

The equivalent CLI commands are:

```bash
tw-market archive-quotes --market TWSE --root market-data
tw-market archive-quotes --market TPEX --root market-data
```

The archive is idempotent for identical bytes and refuses to silently overwrite changed content for the same exchange/date. See `docs/snapshots.md` for the integrity model.

## MCP client

Install the optional MCP dependency and run an in-memory client against the toolkit server:

```bash
python -m pip install -e '.[mcp]'
python examples/mcp_client.py
```

The public MCP surface exposes read-only market utilities, bounded common-equity history, data normalization, and descriptive analytics. It does not expose brokerage credentials, private strategies, trading signals, or order execution.
