"""Taiwan market symbol normalization helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Market(str, Enum):
    """Supported Taiwan cash-equity markets."""

    TWSE = "TWSE"
    TPEx = "TPEx"


_MARKET_ALIASES = {
    "TWSE": Market.TWSE,
    "TW": Market.TWSE,
    "TPEX": Market.TPEx,
    "TWO": Market.TPEx,
    "OTC": Market.TPEx,
}


def normalize_market(value: Market | str) -> Market:
    """Normalize common TWSE/TPEx market aliases into the ``Market`` enum."""
    if isinstance(value, Market):
        return value
    try:
        return _MARKET_ALIASES[value.strip().upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported market: {value!r}") from exc


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
        Optional market hint. Accepted aliases include ``TWSE``/``TW`` and
        ``TPEx``/``TPEX``/``TWO``/``OTC``.
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

    hinted = normalize_market(market) if market is not None else None

    if inferred and hinted and inferred is not hinted:
        raise ValueError(
            f"Ticker suffix implies {inferred.value}, but market hint says {hinted.value}."
        )

    return NormalizedSymbol(code=code, market=inferred or hinted)
