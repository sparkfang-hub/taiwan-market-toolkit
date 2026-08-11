# Data sources and provenance

Taiwan Market Toolkit prefers authoritative public sources and keeps fetching separate from parsing so callers can cache raw payloads for reproducibility.

## Taiwan Stock Exchange (TWSE)

### Holiday schedule

Implemented source:

`https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule`

The toolkit parses the official JSON response into `TWSEHolidayRecord` objects and then builds a `TaiwanTradingCalendar` from explicit open/closure records.

### Current closing snapshot

Implemented source:

`https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`

The toolkit reads the common snapshot fields `Date`, `Code`, `Name`, and `ClosingPrice` and exposes them as a strategy-neutral `ClosingQuote`. Additional exchange-specific fields remain in the raw official payload and are not silently reinterpreted.

## Taipei Exchange (TPEx)

TPEx operates an official OpenAPI platform at:

`https://www.tpex.org.tw/openapi/`

### Current main-board closing snapshot

Implemented source:

`https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`

The common subset exposed by the toolkit is the trading date, security code, company name, market, and closing price. The adapter does not attempt to make TWSE- and TPEx-specific payloads look identical beyond fields with clear common meaning.

### Holiday schedule

TPEx also publishes an official Holiday Schedule section on its website. A dedicated holiday endpoint was not identified in the current OpenAPI specification during the initial implementation work, so the toolkit does not pretend that a generic weekday calendar is authoritative for TPEx holidays.

Issue #2 tracks selection and implementation of the most stable authoritative TPEx holiday source. A future adapter should keep HTML/network fetching separate from parsing if the website schedule remains the best official source.

## Reliability model

Live exchange responses are not required for unit tests. Parser tests use compact fixtures so normal CI remains deterministic, while a separate scheduled/manual GitHub Actions smoke check probes the official sources and fails visibly if the endpoint becomes unavailable or the required schema changes.

Design rules:

- do not copy a holiday table into the package and let it silently go stale;
- keep network fetching separate from parsing;
- allow users to cache exact official payloads for reproducible research;
- keep normal unit tests fixture-based rather than dependent on live exchange uptime;
- probe official sources periodically so upstream schema changes are noticed;
- preserve `None` when an official closing-price field represents no value instead of inventing a numeric price.

## Contribution requirements for new sources

A new source adapter should document:

1. the official publisher and endpoint/page;
2. whether the source is current-state or historical;
3. expected update frequency;
4. schema stability assumptions;
5. cache/reproducibility behavior;
6. licensing or terms-of-use considerations;
7. failure behavior when the source is unavailable or changes format.

Do not commit proprietary datasets, credentials, private brokerage responses, or data that cannot legally be redistributed.
