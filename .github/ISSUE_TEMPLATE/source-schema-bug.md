---
name: Official source or schema problem
about: Report an official TWSE/TPEx endpoint outage, schema change, or parser mismatch
title: "[source] "
labels: bug
aassignees: ""
---

## Source

Exchange: TWSE / TPEx

Endpoint or page:

Observation date and local time (Asia/Taipei if known):

## What changed or failed?

Describe the smallest observable problem. Examples: endpoint unavailable, renamed field, unexpected response shape, date format changed, unit meaning changed, or a valid official row is rejected by the parser.

## Reproduction

Please include the smallest command or Python example that reproduces the problem.

```text
paste command or code here
```

Python version:

Operating system:

Taiwan Market Toolkit version or commit:

## Source evidence

If redistribution is permitted, include the smallest redacted response fragment that demonstrates the issue. Prefer field names and one affected row over a complete market-wide payload.

```json
{}
```

Do not post brokerage credentials, cookies, private account data, proprietary datasets, or secrets.

## Expected behavior

What did you expect the toolkit to return or preserve?

## Additional context

If this appears to be an upstream schema change, note whether the official source still documents the old or new field name/meaning. If the source is merely temporarily unavailable, mention any official outage/status information you found.

The project keeps ordinary unit tests fixture-based. Reproducible source/schema reports are normally converted into a compact regression fixture before parser behavior changes.
