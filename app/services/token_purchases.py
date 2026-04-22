"""Stripe purchase listing and token lifetime aggregates for one user."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from app.models.billing import StripePurchase, TokenTransaction
from app.models.enums import StripeStatus, TokenType, TransactionReason
from app.models.users import User
from app.schemas.tokens import StripePurchaseItem, TokenLifetimeSummaryData

# Ledger convention for `token_transactions.amount`:
#   Credits (purchase, refund credit, manual credit) are positive; debits (job_deduct) are negative.
#   Tokens used = -SUM(amount) for rows with reason == JOB_DEDUCT (non-negative result).


def _purchase_to_item(row: StripePurchase) -> StripePurchaseItem:
    return StripePurchaseItem(
        id=row.id,
        created_at=row.created_at,
        token_type=row.token_type,
        tokens_purchased=row.tokens_purchased,
        amount_cents=row.amount_cents,
        currency=row.currency,
        status=row.status,
        stripe_payment_intent_id=row.stripe_payment_intent_id,
        stripe_session_id=row.stripe_session_id,
    )


def list_stripe_purchases(
    db: Session,
    *,
    user: User,
    token_type: TokenType | None = None,
    status: list[StripeStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[StripePurchaseItem], int]:
    conditions = [StripePurchase.user_id == user.id]
    if token_type is not None:
        conditions.append(StripePurchase.token_type == token_type)
    if status:
        conditions.append(StripePurchase.status.in_(status))
    if created_from is not None:
        conditions.append(StripePurchase.created_at >= created_from)
    if created_to is not None:
        conditions.append(StripePurchase.created_at <= created_to)

    filt = and_(*conditions)

    total = int(db.scalar(select(func.count()).select_from(StripePurchase).where(filt)) or 0)

    offset = (page - 1) * page_size
    list_stmt: Select[tuple[StripePurchase]] = (
        select(StripePurchase)
        .where(filt)
        .order_by(StripePurchase.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.scalars(list_stmt).all()
    return [_purchase_to_item(r) for r in rows], total


def _sum_completed_tokens_purchased(
    db: Session, *, user_id: uuid.UUID, token_type: TokenType
) -> int:
    n = db.scalar(
        select(func.coalesce(func.sum(StripePurchase.tokens_purchased), 0)).where(
            StripePurchase.user_id == user_id,
            StripePurchase.token_type == token_type,
            StripePurchase.status == StripeStatus.COMPLETED,
        )
    )
    return int(n or 0)


def _sum_tokens_used_from_ledger(db: Session, *, user_id: uuid.UUID, token_type: TokenType) -> int:
    n = db.scalar(
        select(func.coalesce(-func.sum(TokenTransaction.amount), 0)).where(
            TokenTransaction.user_id == user_id,
            TokenTransaction.token_type == token_type,
            TokenTransaction.reason == TransactionReason.JOB_DEDUCT,
        )
    )
    return max(0, int(n or 0))


def get_token_lifetime_summary(db: Session, *, user: User) -> TokenLifetimeSummaryData:
    uid = user.id
    return TokenLifetimeSummaryData(
        total_ff_purchased=_sum_completed_tokens_purchased(db, user_id=uid, token_type=TokenType.FF),
        total_ee_purchased=_sum_completed_tokens_purchased(db, user_id=uid, token_type=TokenType.EE),
        ff_tokens_used=_sum_tokens_used_from_ledger(db, user_id=uid, token_type=TokenType.FF),
        ee_tokens_used=_sum_tokens_used_from_ledger(db, user_id=uid, token_type=TokenType.EE),
    )
