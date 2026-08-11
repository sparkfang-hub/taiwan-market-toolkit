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

### Ex-rights/ex-dividend announcements

`https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL`

The current announcement table publishes the ex-rights/ex-dividend date, security code/name, action type, stock-dividend ratio, cash-capital-increase subscription ratio and price, cash dividend, and related subscription-share fields. The toolkit normalizes these fields into `CorporateAction` while retaining the exchange's original action label.

Not-yet-announced values such as an unpublished subscription price remain `None`; a published numeric zero remains zero.

### Individual historical daily prices

`https://www.twse.com.tw/exchangeReport/STOCK_DAY`

The official TWSE historical page exposes individual-security daily trading data by month and states that this dataset is available from 2010-01-04 onward. The toolkit supplies `response=json`, a month anchor in `date`, and `stockNo`, then normalizes ROC dates and the published daily fields into `HistoricalPrice`.

TWSE reports volume in shares and trade value in TWD for this table. Missing price cells are preserved as missing rather than manufactured.

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

### Ex-rights/ex-dividend announcements

`https://www.tpex.org.tw/openapi/v1/tpex_exright_prepost`

The current TPEx preview table publishes the ex-rights/ex-dividend date, security code/name, action type, stock-dividend ratio, cash-capital-increase subscription ratio and price, cash dividend, and public/employee/existing-shareholder subscription fields. These fields map into the same `CorporateAction` model as TWSE announcements.

The implementation was checked against the live official OpenAPI schema before the parser fixtures were written. Scheduled source probes continue to exercise the endpoint independently from deterministic unit tests.

### Individual main-board historical daily prices

`https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock`

The official TPEx historical page exposes individual main-board security history by month and states that data is available from 1994-01 onward. The JSON response contains a `tables` collection whose first table publishes date, trading lots, trade value in thousands, OHLC, change, and transaction count.

For ordinary four-digit common equities, the toolkit converts trading lots to shares and thousands of TWD to TWD by multiplying by 1,000. The v0.1 history adapter deliberately rejects non-four-digit products because ETFs and other instruments can have different trading-unit conventions. It is safer to reject an unsupported product than to produce a plausible-looking but wrong volume series.

### Current valuation snapshot

`https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis`

The toolkit maps published P/E ratio, dividend yield, price-to-book ratio, and dividend per share when present into `ValuationMetrics`.

### Holiday schedule

TPEx publishes an official Holiday Schedule section on its website. A dedicated holiday endpoint was not identified in the current OpenAPI specification during the initial implementation work, so the toolkit does not pretend that a generic weekday calendar is authoritative for TPEx holidays.

Issue #2 tracks selection and implementation of the most stable authoritative TPEx holiday source.

## Reproducible raw snapshots

Current-state APIs do not guarantee that a later request will reproduce an older payload. `SnapshotStore` and `archive_official_closing_snapshot()` preserve exact closing-response bytes under deterministic source/date paths with SHA-256 metadata. Identical writes are idempotent; changed same-date content is rejected unless replacement is explicit.

Downloaded market payloads are not committed to the repository by default. See `docs/snapshots.md`.

Historical price fetching is intentionally paced and bounded. Applications that need large ranges should cache completed months locally rather than repeatedly requesting unchanged history from public exchange services.

## Reliability model

Live exchange responses are not required for unit tests. Parser tests use compact fixtures so CI stays deterministic, while a separate scheduled/manual GitHub Actions smoke check probes implemented official sources and fails visibly if an endpoint disappears or required fields drift.

Design rules:

- keep network fetching separate from parsing;
- keep unified models narrow and only map fields with clear meaning;
- preserve missing values rather than inventing zeroes;
- preserve source values such as industry codes instead of guessing labels;
- normalize exchange units only when their meaning is explicit for the supported product type;
- reject ambiguous product-unit conversions rather than guessing;
- cache exact raw payloads when reproducibility matters;
- do not silently overwrite changed historical snapshots;
- do not ship stale copied holiday tables as if they were authoritative;
- pace and bound repeated historical requests to public exchange endpoints;
- keep ordinary tests fixture-based rather than dependent on exchange uptime;
- probe live official sources separately for schema/availability drift.

## Contribution requirements for new sources

A new source adapter should document:

1. official publisher and endpoint/page;
2. whether the source is current-state or historical;
3. expected update frequency;
4. schema stability assumptions;
5. source units and any normalization rules;
6. cache/reproducibility behavior;
7. licensing or terms-of-use considerations;
8. failure behavior when the source is unavailable or changes format.

Do not commit proprietary datasets, credentials, private brokerage responses, or data that cannot legally be redistributed.
