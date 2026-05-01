from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_stub_token_credit_enabled
from app.core.fast_fill_token_prices import FAST_FILL_TOKEN_PACKAGES
from app.db.session import get_db
from app.models.enums import StripeStatus, TokenType
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.tokens import (
    FastFillTokenPackageOut,
    FastFillTokenPackagesData,
    StripePurchasePage,
    StubTokenCreditIn,
    StubTokenCreditOut,
    TokenLifetimeSummaryData,
)
from app.services.stub_token_credit import credit_wallet_stub
from app.services.token_purchases import get_token_lifetime_summary, list_stripe_purchases

router = APIRouter()


@router.get(
    "/tokens",
    summary="Fast Fill token package pricing",
    description="Public catalog of Fast Fill token bundles and USD prices.",
)
def list_fast_fill_token_packages() -> SuccessEnvelope[FastFillTokenPackagesData]:
    packages = [
        FastFillTokenPackageOut(
            tokens=p.tokens,
            total_usd=p.total_usd,
            price_per_token_usd=p.price_per_token_usd,
        )
        for p in FAST_FILL_TOKEN_PACKAGES
    ]
    return SuccessEnvelope(message="OK", data=FastFillTokenPackagesData(packages=packages))


@router.get(
    "/tokens/purchases",
    summary="Stripe token purchase history",
    description=(
        "Paginated `stripe_purchases` for the signed-in user. Filter by `token_type` (ee | ff), "
        "`status` (repeat param), and `created_from` / `created_to`."
    ),
)
def get_token_purchase_history(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    token_type: TokenType | None = Query(
        default=None,
        description="Optional: only ee or ff. Omit for both.",
    ),
    status: list[StripeStatus] | None = Query(
        default=None,
        description="Filter by Stripe purchase status (repeat param for multiple). Omit for any status.",
    ),
    created_from: datetime | None = Query(
        default=None,
        description="Include rows with created_at >= this instant (timezone-aware ISO 8601).",
    ),
    created_to: datetime | None = Query(
        default=None,
        description="Include rows with created_at <= this instant.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[StripePurchasePage]:
    items, total = list_stripe_purchases(
        db,
        user=user,
        token_type=token_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        page=page,
        page_size=page_size,
    )
    return SuccessEnvelope(
        message="OK",
        data=StripePurchasePage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/tokens/lifetime",
    summary="Lifetime token purchases and usage",
    description=(
        "Totals: purchased tokens from completed Stripe rows per type; used tokens from "
        "`token_transactions` with reason `job_deduct` (ledger amounts: credits positive, debits negative)."
    ),
)
def get_token_lifetime(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[TokenLifetimeSummaryData]:
    data = get_token_lifetime_summary(db, user=user)
    return SuccessEnvelope(message="OK", data=data)


@router.post(
    "/tokens/stub/credit",
    summary="Stub: credit tokens (no Stripe)",
    description=(
        "Adds tokens to the signed-in user's wallet and records a `manual_adjustment` ledger row. "
        "Only when `STUB_TOKEN_CREDIT_ENABLED=true`. Replace with Stripe in production when ready."
    ),
)
def post_stub_token_credit(
    body: StubTokenCreditIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    _: None = Depends(require_stub_token_credit_enabled),
) -> SuccessEnvelope[StubTokenCreditOut]:
    credited, ff_bal, ee_bal, purchase_id, pi_id, cs_id = credit_wallet_stub(
        db,
        user=user,
        token_type=body.token_type,
        amount=body.amount,
    )
    return SuccessEnvelope(
        message="OK",
        data=StubTokenCreditOut(
            token_type=body.token_type,
            credited=credited,
            ff_balance=ff_bal,
            ee_balance=ee_bal,
            purchase_id=purchase_id,
            stripe_payment_intent_id=pi_id,
            stripe_session_id=cs_id,
        ),
    )
