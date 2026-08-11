"""Validate a Taiwan-style OHLCV CSV with Traditional Chinese headers and ROC dates."""

from pathlib import Path

from taiwan_market_toolkit import read_ohlcv_csv, validate_ohlcv

sample = Path(__file__).with_name("sample_ohlcv_zh.csv")
rows = read_ohlcv_csv(sample)
issues = validate_ohlcv(rows)

print(f"rows={len(rows)}")
print(f"valid={not issues}")
for row in rows:
    print(row)
for issue in issues:
    print(issue)
