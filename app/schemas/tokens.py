from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import StripeStatus, TokenType


class FastFillTokenPackageOut(BaseModel):
    """Fast Fill bundle exposed to clients."""

    product: str = Field(default="Fast Fill", description="Product line for these tokens.")
    tokens: int = Field(ge=1, description="Number of tokens in the bundle.")
    total_usd: Decimal = Field(description="Total price for the bundle in USD.")
    price_per_token_usd: Decimal = Field(description="List price per token in USD.")


class FastFillTokenPackagesData(BaseModel):
    packages: list[FastFillTokenPackageOut]


class StripePurchaseItem(BaseModel):
    """One Stripe checkout row for the authenticated user."""

    id: uuid.UUID
    created_at: datetime
    token_type: TokenType
    tokens_purchased: int = Field(ge=0)
    amount_cents: int = Field(ge=0)
    currency: str
    status: StripeStatus
    stripe_payment_intent_id: str
    stripe_session_id: str


class StripePurchasePage(BaseModel):
    items: list[StripePurchaseItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class TokenLifetimeSummaryData(BaseModel):
    """Lifetime token totals: purchases from completed Stripe rows; usage from ledger job deductions."""

    total_ff_purchased: int = Field(ge=0, description="Sum of tokens from completed FF Stripe purchases.")
    total_ee_purchased: int = Field(ge=0, description="Sum of tokens from completed EE Stripe purchases.")
    ff_tokens_used: int = Field(ge=0, description="Tokens debited for FF jobs (see ledger sign convention).")
    ee_tokens_used: int = Field(ge=0, description="Tokens debited for EE jobs (see ledger sign convention).")


class StubTokenCreditIn(BaseModel):
    """Body for stub credit (requires STUB_TOKEN_CREDIT_ENABLED)."""

    token_type: TokenType = Field(description="ee or ff balance to increase.")
    amount: int = Field(ge=1, le=10_000, description="Tokens to credit in one call (capped for safety).")


class StubTokenCreditOut(BaseModel):
    token_type: TokenType
    credited: int = Field(ge=1)
    ff_balance: int = Field(ge=0)
    ee_balance: int = Field(ge=0)
    purchase_id: uuid.UUID = Field(description="Row in `stripe_purchases` (stub ids until real Stripe).")
    stripe_payment_intent_id: str
    stripe_session_id: str
