"""Debit token wallet when a billable job action occurs (ledger + balance)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.billing import TokenTransaction, TokenWallet
from app.models.enums import TokenType, TransactionReason


class InsufficientTokensError(Exception):
    """Raised when wallet balance is below required debit."""

    def __init__(self, *, token_type: TokenType, required: int, available: int) -> None:
        self.token_type = token_type
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {token_type.value} tokens (need {required}, have {available}).",
        )


def debit_job_tokens(
    db: Session,
    *,
    wallet_user_id: uuid.UUID,
    job_id: uuid.UUID,
    token_type: TokenType,
    amount: int,
) -> None:
    """
    Row-lock wallet, ensure balance >= amount, decrement, append `job_deduct` (negative amount).

    Caller must commit. No-op when amount <= 0. Missing wallet row is treated as zero balance.
    """
    if amount <= 0:
        return

    wallet = db.scalar(
        select(TokenWallet)
        .where(TokenWallet.user_id == wallet_user_id)
        .with_for_update(),
    )
    if wallet is None:
        raise InsufficientTokensError(token_type=token_type, required=amount, available=0)

    if token_type == TokenType.EE:
        available = int(wallet.ee_balance)
    else:
        available = int(wallet.ff_balance)

    if available < amount:
        raise InsufficientTokensError(token_type=token_type, required=amount, available=available)

    if token_type == TokenType.EE:
        wallet.ee_balance = available - amount
    else:
        wallet.ff_balance = available - amount

    db.add(
        TokenTransaction(
            user_id=wallet_user_id,
            job_id=job_id,
            token_type=token_type,
            amount=-amount,
            reason=TransactionReason.JOB_DEDUCT,
            stripe_payment_intent_id=None,
            notes=None,
        )
    )


def ee_submit_token_cost() -> int:
    return int(get_settings().ee_job_submit_token_cost)


def ff_submit_token_cost() -> int:
    return int(get_settings().ff_job_submit_token_cost)
