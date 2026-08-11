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

## MCP client

Install the optional MCP dependency and run an in-memory client against the toolkit server:

```bash
python -m pip install -e '.[mcp]'
python examples/mcp_client.py
```

The public MCP surface exposes data-normalization and calendar utilities only. It does not expose brokerage credentials, private strategies, trading signals, or order execution.
