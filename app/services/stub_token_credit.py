"""Dev-only wallet credits until Stripe checkout is implemented."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billing import StripePurchase, TokenTransaction, TokenWallet
from app.models.enums import StripeStatus, TokenType, TransactionReason
from app.models.users import User


def credit_wallet_stub(
    db: Session,
    *,
    user: User,
    token_type: TokenType,
    amount: int,
) -> tuple[int, int, int, uuid.UUID, str, str]:
    """
    Mirror real flow: completed `stripe_purchases` row, wallet bump, `purchase` ledger line.

    Stub Stripe ids are unique (`stub_pi_*` / `stub_cs_*`) so purchase history and lifetime
    totals (`GET /tokens/purchases`, `GET /tokens/lifetime`) behave like production.

    Returns (credited_amount, ff_balance_after, ee_balance_after, purchase_id, pi_id, cs_id).
    """
    u = uuid.uuid4()
    stripe_payment_intent_id = f"stub_pi_{u.hex}"
    stripe_session_id = f"stub_cs_{u.hex}"

    wallet = db.scalar(select(TokenWallet).where(TokenWallet.user_id == user.id))
    if wallet is None:
        wallet = TokenWallet(user_id=user.id, ee_balance=0, ff_balance=0)
        db.add(wallet)
        db.flush()

    purchase = StripePurchase(
        user_id=user.id,
        stripe_payment_intent_id=stripe_payment_intent_id,
        stripe_session_id=stripe_session_id,
        token_type=token_type,
        tokens_purchased=amount,
        amount_cents=0,
        currency="usd",
        status=StripeStatus.COMPLETED,
    )
    db.add(purchase)
    db.flush()

    if token_type == TokenType.FF:
        wallet.ff_balance = int(wallet.ff_balance) + amount
    else:
        wallet.ee_balance = int(wallet.ee_balance) + amount

    db.add(
        TokenTransaction(
            user_id=user.id,
            job_id=None,
            token_type=token_type,
            amount=amount,
            reason=TransactionReason.PURCHASE,
            stripe_payment_intent_id=stripe_payment_intent_id,
            notes="stub purchase until Stripe checkout is wired",
        )
    )
    db.flush()
    return (
        amount,
        int(wallet.ff_balance),
        int(wallet.ee_balance),
        purchase.id,
        stripe_payment_intent_id,
        stripe_session_id,
    )
