# Data sources and provenance

Taiwan Market Toolkit prefers authoritative public sources and keeps fetching separate from parsing so callers can cache raw payloads for reproducibility.

## Taiwan Stock Exchange (TWSE)

### Listed-company basic data

`https://openapi.twse.com.tw/v1/opendata/t187ap03_L`

Stable identity fields are mapped into the common `SecurityProfile` model. Exchange-specific disclosure fields remain outside the common model.

### Holiday schedule

`https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule`

The JSON response is parsed into `TWSEHolidayRecord` objects and then into explicit calendar open/closure overrides.

### Current closing snapshot

`https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`

The toolkit exposes the common fields date, code, name, market, and closing price as `ClosingQuote`.

### Current valuation snapshot

`https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL`

The toolkit maps published P/E ratio, dividend yield, and price-to-book ratio into `ValuationMetrics`. Missing/non-calculated values remain `None`.

## Taipei Exchange (TPEx)

TPEx operates an official OpenAPI platform at `https://www.tpex.org.tw/openapi/`.

### Main-board company basic data

`https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O`

Company code, names, industry code, and listing date are mapped into the same `SecurityProfile` model used for TWSE identities.

### Current main-board closing snapshot

`https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`

The common subset is date, security code, company name, market, and closing price.

### Current valuation snapshot

`https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis`

The toolkit maps published P/E ratio, dividend yield, price-to-book ratio, and dividend per share when present into `ValuationMetrics`.

### Holiday schedule

TPEx publishes an official Holiday Schedule section on its website. A dedicated holiday endpoint was not identified in the current OpenAPI specification during the initial implementation work, so the toolkit does not pretend that a generic weekday calendar is authoritative for TPEx holidays.

Issue #2 tracks selection and implementation of the most stable authoritative TPEx holiday source.

## Reproducible raw snapshots

Current-state APIs do not guarantee that a later request will reproduce an older payload. `SnapshotStore` and `archive_official_closing_snapshot()` preserve exact closing-response bytes under deterministic source/date paths with SHA-256 metadata. Identical writes are idempotent; changed same-date content is rejected unless replacement is explicit.

Downloaded market payloads are not committed to the repository by default. See `docs/snapshots.md`.

## Reliability model

Live exchange responses are not required for unit tests. Parser tests use compact fixtures so CI stays deterministic, while a separate scheduled/manual GitHub Actions smoke check probes implemented official sources and fails visibly if an endpoint disappears or required fields drift.

Design rules:

- keep network fetching separate from parsing;
- keep unified models narrow and only map fields with clear meaning;
- preserve missing values rather than inventing zeroes;
- preserve source values such as industry codes instead of guessing labels;
- cache exact raw payloads when reproducibility matters;
- do not silently overwrite changed historical snapshots;
- do not ship stale copied holiday tables as if they were authoritative;
- keep ordinary tests fixture-based rather than dependent on exchange uptime;
- probe live official sources separately for schema/availability drift.

## Contribution requirements for new sources

A new source adapter should document:

1. official publisher and endpoint/page;
2. whether the source is current-state or historical;
3. expected update frequency;
4. schema stability assumptions;
5. cache/reproducibility behavior;
6. licensing or terms-of-use considerations;
7. failure behavior when the source is unavailable or changes format.

Do not commit proprietary datasets, credentials, private brokerage responses, or data that cannot legally be redistributed.
