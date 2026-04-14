from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._sqltypes import pg_enum
from app.models.enums import FfPdfType, JobStatus, JobType
from app.models.users import User


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_user_id", "user_id"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_status_created_at", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_type: Mapped[JobType] = mapped_column(pg_enum(JobType, "job_type_enum"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(pg_enum(JobStatus, "job_status_enum"), nullable=False)

    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="jobs")
    details_ee: Mapped[JobDetailsEE | None] = relationship(back_populates="job", uselist=False)
    details_ff: Mapped[JobDetailsFF | None] = relationship(back_populates="job", uselist=False)
    status_history: Mapped[list[JobStatusHistory]] = relationship(back_populates="job")
    token_transactions: Mapped[list["TokenTransaction"]] = relationship(
        "TokenTransaction",
        back_populates="job",
    )


class JobDetailsEE(Base):
    __tablename__ = "job_details_ee"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    output_file_key: Mapped[str | None] = mapped_column(String, nullable=True)
    output_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[Job] = relationship(back_populates="details_ee")


class JobDetailsFF(Base):
    __tablename__ = "job_details_ff"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    ff_pdf_type: Mapped[FfPdfType] = mapped_column(pg_enum(FfPdfType, "ff_pdf_type_enum"), nullable=False)
    pdf_file_key: Mapped[str | None] = mapped_column(String, nullable=True)
    esx_file_key: Mapped[str | None] = mapped_column(String, nullable=True)
    output_file_key: Mapped[str | None] = mapped_column(String, nullable=True)
    output_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[Job] = relationship(back_populates="details_ff")


class JobStatusHistory(Base):
    __tablename__ = "job_status_history"
    __table_args__ = (Index("ix_job_status_history_job_id", "job_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    from_status: Mapped[JobStatus | None] = mapped_column(pg_enum(JobStatus, "job_status_enum"), nullable=True)
    to_status: Mapped[JobStatus] = mapped_column(pg_enum(JobStatus, "job_status_enum"), nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped[Job] = relationship(back_populates="status_history")
