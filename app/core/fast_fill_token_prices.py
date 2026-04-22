"""Catalog prices for Fast Fill token bundles (USD).

Edit the FAST_FILL_* constants below when list prices change.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# --- 10 tokens ---
FAST_FILL_10_TOKEN_COUNT = 10
FAST_FILL_10_TOTAL_USD = Decimal("149.9")
FAST_FILL_10_PRICE_PER_TOKEN_USD = Decimal("14.99")

# --- 25 tokens ---
FAST_FILL_25_TOKEN_COUNT = 25
FAST_FILL_25_TOTAL_USD = Decimal("337.25")
FAST_FILL_25_PRICE_PER_TOKEN_USD = Decimal("13.49")

# --- 50 tokens ---
FAST_FILL_50_TOKEN_COUNT = 50
FAST_FILL_50_TOTAL_USD = Decimal("599.6")
FAST_FILL_50_PRICE_PER_TOKEN_USD = Decimal("11.99")

# --- 100 tokens ---
FAST_FILL_100_TOKEN_COUNT = 100
FAST_FILL_100_TOTAL_USD = Decimal("1049.3")
FAST_FILL_100_PRICE_PER_TOKEN_USD = Decimal("10.49")


@dataclass(frozen=True, slots=True)
class FastFillTokenPackage:
    """One purchasable Fast Fill token tier."""

    tokens: int
    total_usd: Decimal
    price_per_token_usd: Decimal


FAST_FILL_TOKEN_PACKAGES: tuple[FastFillTokenPackage, ...] = (
    FastFillTokenPackage(
        tokens=FAST_FILL_10_TOKEN_COUNT,
        total_usd=FAST_FILL_10_TOTAL_USD,
        price_per_token_usd=FAST_FILL_10_PRICE_PER_TOKEN_USD,
    ),
    FastFillTokenPackage(
        tokens=FAST_FILL_25_TOKEN_COUNT,
        total_usd=FAST_FILL_25_TOTAL_USD,
        price_per_token_usd=FAST_FILL_25_PRICE_PER_TOKEN_USD,
    ),
    FastFillTokenPackage(
        tokens=FAST_FILL_50_TOKEN_COUNT,
        total_usd=FAST_FILL_50_TOTAL_USD,
        price_per_token_usd=FAST_FILL_50_PRICE_PER_TOKEN_USD,
    ),
    FastFillTokenPackage(
        tokens=FAST_FILL_100_TOKEN_COUNT,
        total_usd=FAST_FILL_100_TOTAL_USD,
        price_per_token_usd=FAST_FILL_100_PRICE_PER_TOKEN_USD,
    ),
)
