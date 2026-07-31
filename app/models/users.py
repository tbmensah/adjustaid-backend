from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._sqltypes import pg_enum
from app.models.enums import UserType

# Supabase Auth (`auth.users`) — minimal stub so FK resolution works; Auth owns this table.
auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)

if TYPE_CHECKING:
    from app.models.billing import StripePurchase, TokenTransaction, TokenWallet
    from app.models.jobs import Job


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(auth_users.c.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str | None] = mapped_column(String, nullable=True)
    user_type: Mapped[UserType] = mapped_column(
        pg_enum(UserType, "user_type_enum"),
        nullable=False,
        default=UserType.CUSTOMER,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    wallet: Mapped[TokenWallet | None] = relationship(back_populates="user", uselist=False)
    token_transactions: Mapped[list[TokenTransaction]] = relationship(back_populates="user")
    stripe_purchases: Mapped[list[StripePurchase]] = relationship(back_populates="user")
    jobs: Mapped[list[Job]] = relationship(back_populates="user")
