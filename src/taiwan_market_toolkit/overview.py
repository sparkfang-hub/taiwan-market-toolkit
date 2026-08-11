"""Compose official identity, closing-quote, and valuation data for one security.

The overview preserves each source model and its own observation date instead of
pretending that independently published datasets are synchronized.
"""

from __future__ import annotations

from dataclasses import dataclass

from .directory import SecurityProfile, find_company
from .quotes import ClosingQuote, fetch_closing_quote
from .symbols import Market, normalize_symbol
from .valuation import ValuationMetrics, find_valuation


@dataclass(frozen=True, slots=True)
class SecurityOverview:
    """Read-only official-data overview for one Taiwan security."""

    profile: SecurityProfile
    quote: ClosingQuote
    valuation: ValuationMetrics

    def __post_init__(self) -> None:
        """Reject accidentally combined data from different securities or markets."""
        identities = {
            (self.profile.market, self.profile.code),
            (self.quote.market, self.quote.code),
            (self.valuation.market, self.valuation.code),
        }
        if len(identities) != 1:
            raise ValueError("overview components must refer to the same market and code")

    @property
    def market(self) -> Market:
        return self.profile.market

    @property
    def code(self) -> str:
        return self.profile.code

    @property
    def yahoo(self) -> str:
        return self.profile.yahoo


def fetch_security_overview(
    value: str,
    market: Market | str | None = None,
    *,
    timeout: float = 10.0,
) -> SecurityOverview:
    """Fetch official company, close, and valuation data for one security.

    Bare symbols require an explicit market. Each underlying adapter remains
    independently testable and retains its own source-specific observation date.
    """
    symbol = normalize_symbol(value, market)
    if symbol.market is None:
        raise ValueError("market is required for a bare Taiwan ticker")

    market_hint = symbol.market
    code = symbol.code

    profile = find_company(code, market_hint, timeout=timeout)
    quote = fetch_closing_quote(code, market_hint, timeout=timeout)
    valuation = find_valuation(code, market_hint, timeout=timeout)

    return SecurityOverview(profile=profile, quote=quote, valuation=valuation)
