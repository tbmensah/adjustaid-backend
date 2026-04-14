from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._sqltypes import pg_enum
from app.models.enums import StripeStatus, TokenType, TransactionReason
from app.models.users import User


class TokenWallet(Base):
    __tablename__ = "token_wallets"
    __table_args__ = (UniqueConstraint("user_id", name="uq_token_wallets_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ee_balance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    ff_balance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="wallet")


class TokenTransaction(Base):
    __tablename__ = "token_transactions"
    __table_args__ = (
        Index("ix_token_transactions_user_id", "user_id"),
        Index("ix_token_transactions_job_id", "job_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    token_type: Mapped[TokenType] = mapped_column(pg_enum(TokenType, "token_type_enum"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[TransactionReason] = mapped_column(
        pg_enum(TransactionReason, "transaction_reason_enum"),
        nullable=False,
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="token_transactions")
    job: Mapped["Job | None"] = relationship("Job", back_populates="token_transactions")


class StripePurchase(Base):
    __tablename__ = "stripe_purchases"
    __table_args__ = (Index("ix_stripe_purchases_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    stripe_session_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    token_type: Mapped[TokenType] = mapped_column(pg_enum(TokenType, "token_type_enum"), nullable=False)
    tokens_purchased: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, server_default="usd")
    status: Mapped[StripeStatus] = mapped_column(pg_enum(StripeStatus, "stripe_status_enum"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="stripe_purchases")
