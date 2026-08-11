"""Taiwan market symbol normalization helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Market(str, Enum):
    """Supported Taiwan cash-equity markets."""

    TWSE = "TWSE"
    TPEx = "TPEx"


@dataclass(frozen=True, slots=True)
class NormalizedSymbol:
    """Normalized representation of a Taiwan-listed security symbol."""

    code: str
    market: Market | None

    @property
    def yahoo(self) -> str:
        """Return a Yahoo Finance style ticker when the market is known."""
        if self.market is Market.TWSE:
            return f"{self.code}.TW"
        if self.market is Market.TPEx:
            return f"{self.code}.TWO"
        return self.code


def normalize_symbol(value: str, market: Market | str | None = None) -> NormalizedSymbol:
    """Normalize Taiwan stock tickers such as ``2330``, ``2330.TW`` or ``6488.TWO``.

    Parameters
    ----------
    value:
        Raw ticker string.
    market:
        Optional market hint. Accepted values are ``TWSE`` and ``TPEx``.
    """
    raw = value.strip().upper()
    match = re.fullmatch(r"([0-9A-Z]{4,6})(?:\.(TW|TWO))?", raw)
    if not match:
        raise ValueError(f"Unsupported Taiwan market symbol: {value!r}")

    code, suffix = match.groups()

    inferred: Market | None = None
    if suffix == "TW":
        inferred = Market.TWSE
    elif suffix == "TWO":
        inferred = Market.TPEx

    hinted: Market | None = None
    if market is not None:
        if isinstance(market, Market):
            hinted = market
        else:
            normalized_market = market.strip().upper()
            aliases = {
                "TWSE": Market.TWSE,
                "TW": Market.TWSE,
                "TPEX": Market.TPEx,
                "TWO": Market.TPEx,
                "OTC": Market.TPEx,
            }
            try:
                hinted = aliases[normalized_market]
            except KeyError as exc:
                raise ValueError(f"Unsupported market: {market!r}") from exc

    if inferred and hinted and inferred is not hinted:
        raise ValueError(
            f"Ticker suffix implies {inferred.value}, but market hint says {hinted.value}."
        )

    return NormalizedSymbol(code=code, market=inferred or hinted)
