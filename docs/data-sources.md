# Data sources and provenance

Taiwan Market Toolkit prefers authoritative public sources and keeps fetching separate from parsing so callers can cache raw payloads for reproducibility.

## Taiwan Stock Exchange (TWSE)

### Listed-company basic data

Implemented source:

`https://openapi.twse.com.tw/v1/opendata/t187ap03_L`

The toolkit maps stable identity fields such as company code, company name, abbreviation, English name, industry code, and listing date into the common `SecurityProfile` model. Exchange-specific disclosure fields remain outside the common model.

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

### Main-board company basic data

Implemented source:

`https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O`

The toolkit maps TPEx company-code, company-name, abbreviation, English symbol/name, industry code, and listing-date fields into the same `SecurityProfile` model used for TWSE identities. This unification is intentionally limited to fields with clear shared semantics.

### Current main-board closing snapshot

Implemented source:

`https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`

The common subset exposed by the toolkit is the trading date, security code, company name, market, and closing price. The adapter does not attempt to make TWSE- and TPEx-specific payloads look identical beyond fields with clear common meaning.

### Holiday schedule

TPEx also publishes an official Holiday Schedule section on its website. A dedicated holiday endpoint was not identified in the current OpenAPI specification during the initial implementation work, so the toolkit does not pretend that a generic weekday calendar is authoritative for TPEx holidays.

Issue #2 tracks selection and implementation of the most stable authoritative TPEx holiday source. A future adapter should keep HTML/network fetching separate from parsing if the website schedule remains the best official source.

## Reproducible raw snapshots

Current-state APIs are useful for live tooling but do not guarantee that a future request will reproduce the payload seen by a previous research run. The toolkit therefore exposes raw-response fetchers and a local `SnapshotStore`.

`archive_official_closing_snapshot()` preserves the exact official response bytes under deterministic source/date paths and records a SHA-256 digest. Identical repeated writes are idempotent. Different content for an already archived source/date is rejected unless replacement is explicitly requested.

The archive intentionally remains local and separate from the package source tree. Downloaded market payloads are not committed to the repository by default. See `docs/snapshots.md` for the storage and integrity model.

## Reliability model

Live exchange responses are not required for unit tests. Parser tests use compact fixtures so normal CI remains deterministic, while a separate scheduled/manual GitHub Actions smoke check probes the official sources and fails visibly if an endpoint becomes unavailable or required identity/quote fields drift.

Design rules:

- do not copy a holiday table into the package and let it silently go stale;
- keep network fetching separate from parsing;
- preserve exact raw payloads when reproducibility matters;
- allow users to cache official payloads without coupling the core package to a database;
- keep normal unit tests fixture-based rather than dependent on live exchange uptime;
- probe official sources periodically so upstream schema changes are noticed;
- keep unified models narrow and preserve source values such as industry codes instead of guessing labels;
- preserve `None` when an official closing-price field represents no value instead of inventing a numeric price;
- never silently overwrite a changed historical snapshot for the same source/date.

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
