"""Taiwan Market Toolkit public API."""

from .calendar import TaiwanTradingCalendar
from .normalize import (
    NormalizationResult,
    dataframe_to_ohlcv,
    infer_column_map,
    normalize_and_validate_ohlcv_records,
    normalize_ohlcv_records,
    parse_ohlcv_csv,
    read_ohlcv_csv,
)
from .symbols import Market, NormalizedSymbol, normalize_symbol
from .twse import (
    TWSEHolidayRecord,
    calendar_from_twse_records,
    fetch_twse_calendar,
    fetch_twse_holiday_schedule,
    parse_roc_date,
    parse_twse_holiday_payload,
)
from .validation import OHLCVRow, ValidationIssue, validate_ohlcv

__all__ = [
    "Market",
    "NormalizedSymbol",
    "NormalizationResult",
    "OHLCVRow",
    "TWSEHolidayRecord",
    "TaiwanTradingCalendar",
    "ValidationIssue",
    "calendar_from_twse_records",
    "dataframe_to_ohlcv",
    "fetch_twse_calendar",
    "fetch_twse_holiday_schedule",
    "infer_column_map",
    "normalize_and_validate_ohlcv_records",
    "normalize_ohlcv_records",
    "normalize_symbol",
    "parse_ohlcv_csv",
    "parse_roc_date",
    "parse_twse_holiday_payload",
    "read_ohlcv_csv",
    "validate_ohlcv",
]

__version__ = "0.1.0"
