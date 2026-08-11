# Unified TWSE and TPEx company directory

Taiwan Market Toolkit exposes a small common company/security identity model across the official TWSE and TPEx basic-data datasets.

## Official sources

Listed companies use the TWSE OpenAPI dataset:

```text
https://openapi.twse.com.tw/v1/opendata/t187ap03_L
```

TPEx main-board companies use:

```text
https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O
```

The two sources do not use identical field names. The parser maps fields with the same clear semantic meaning into `SecurityProfile` while leaving exchange-specific disclosure fields outside the common model.

## Common model

`SecurityProfile` contains:

- `market`: TWSE or TPEx;
- `code`: security/company code;
- `name`: company name;
- `short_name`: company abbreviation;
- `english_name`: available English name or symbol;
- `industry`: exchange/MOPS industry code as published by the source;
- `listing_date`: parsed listing date when available;
- `yahoo`: convenience ticker generated from the known market.

Industry is intentionally preserved as the published source value. The toolkit does not guess an industry label from a numeric code.

## Fetch one profile

```python
from taiwan_market_toolkit import find_company

profile = find_company("2330.TW")
print(profile.short_name)
print(profile.industry)
print(profile.listing_date)
```

Bare codes require an explicit market to avoid silently choosing the wrong exchange:

```python
profile = find_company("6488", "TPEX")
```

## Fetch and search the combined directory

```python
from taiwan_market_toolkit import fetch_company_directory, search_company_directory

profiles = fetch_company_directory()
for profile in search_company_directory(profiles, "台積"):
    print(profile.code, profile.short_name, profile.market)
```

The local search ranks exact code matches first, then code prefixes, exact names, and name substrings. It searches company name, abbreviation, and English name and does not perform another network request.

## CLI

```bash
tw-market company 2330.TW
tw-market company 6488 --market TPEX
tw-market search-company 台積
tw-market search-company global --market TPEX --limit 5
```

## Reliability boundary

Network fetching and payload parsing are separate. Unit tests use fixtures, while the scheduled official-source smoke workflow checks that the live TWSE and TPEx company datasets still return parseable rows.

The common model is deliberately narrow. New fields should be added only when their meaning is stable and can be represented consistently without inventing cross-exchange equivalence.
