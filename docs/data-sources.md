# Data sources and provenance

Taiwan Market Toolkit prefers authoritative public sources and keeps fetching separate from parsing so callers can cache raw payloads for reproducibility.

## Taiwan Stock Exchange (TWSE)

### Holiday schedule

Implemented source:

`https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule`

The toolkit parses the official JSON response into `TWSEHolidayRecord` objects and then builds a `TaiwanTradingCalendar` from explicit open/closure records.

Design rules:

- do not copy a holiday table into the package and let it silently go stale;
- keep network fetching optional;
- allow users to cache the exact official response used in research;
- keep parser tests fixture-based so CI does not depend on live network availability.

## Taipei Exchange (TPEx)

TPEx operates an official OpenAPI platform at:

`https://www.tpex.org.tw/openapi/`

The current public specification exposes many machine-readable market datasets, including main-board quotes, securities information, margin data, index data, and other market information.

TPEx also publishes an official Holiday Schedule section on its website. A dedicated holiday endpoint was not identified in the current OpenAPI specification during the initial implementation work, so the toolkit does not pretend that a generic weekday calendar is authoritative for TPEx holidays.

Issue #2 tracks selection and implementation of the most stable authoritative TPEx holiday source. A future adapter should keep HTML/network fetching separate from parsing if the website schedule remains the best official source.

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
