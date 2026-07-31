from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user, require_back_office
from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.supabase_admin import create_signed_download_url
from app.models.enums import JobStatus, JobType, UserType
from app.models.jobs import Job, JobStatusHistory
from app.models.users import User
from app.schemas.ee_job import (
    EeJobCreatedData,
    EeJobDetail,
    EeJobDownloadData,
    EeOutputConfirmBody,
    EeOutputUploadUrlBody,
    EeOutputUploadUrlData,
)
from app.schemas.ee_payload import ExpressEstimatePayload
from app.schemas.envelope import SuccessEnvelope
from app.services.ee_job_create import create_ee_job_from_payload
from app.services.job_token_debit import InsufficientTokensError
from app.services.ee_output_upload import (
    build_readable_input_excel_key,
    build_readable_input_key,
    confirm_output_upload,
    ee_output_bucket,
    ee_readable_bucket,
    ensure_readable_input_excel,
    input_render_exists,
    input_render_excel_exists,
    issue_output_upload_url,
    store_readable_input,
)

logger = logging.getLogger(__name__)

# EE routes: any authenticated user may create jobs; back_office also processes any job.
# Readable `payload.md` upload/download is back-office only.
router = APIRouter()

_EXCEL_FORMAT_ALIASES = frozenset({"excel", "xlsx", "spreadsheet", "sheet", "sheets"})
_MARKDOWN_FORMAT_ALIASES = frozenset({"markdown", "md", "text"})


def _coerce_input_download_format(raw: str) -> Literal["markdown", "excel"]:
    key = (raw or "markdown").strip().lower()
    if key in _EXCEL_FORMAT_ALIASES:
        return "excel"
    if key in _MARKDOWN_FORMAT_ALIASES or key == "":
        return "markdown"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unknown format={raw!r}. Use markdown, md, excel, xlsx, or spreadsheet.",
    )


def _get_ee_job(db: Session, actor: User, job_id: uuid.UUID) -> Job | None:
    """Customer: own EE jobs only. Back office: any EE job (paths still use job owner's user_id)."""
    stmt = (
        select(Job)
        .where(
            Job.id == job_id,
            Job.job_type == JobType.EE,
        )
        .options(selectinload(Job.details_ee))
    )
    if actor.user_type != UserType.BACK_OFFICE:
        stmt = stmt.where(Job.user_id == actor.id)
    return db.scalars(stmt).first()


def _ee_job_detail(job: Job, *, has_input_render: bool, has_input_excel: bool) -> EeJobDetail:
    de = job.details_ee
    if de is None:
        msg = "EE job missing details row"
        raise RuntimeError(msg)
    return EeJobDetail(
        job_id=job.id,
        status=job.status,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        output_ready=bool(de.output_file_key and str(de.output_file_key).strip()),
        has_input_render=has_input_render,
        has_input_excel=has_input_excel,
        error_message=job.error_message,
    )


@router.post(
    "/jobs/ee",
    summary="Submit Express Estimate (JSON object → JSONB)",
    description=(
        "Express Estimate wizard JSON (camelCase keys). `projectDetails.insuredName` and "
        "`projectDetails.claimNumber` required; other sections optional; unknown keys rejected. "
        "Stored in `job_details_ee.payload`. Readable `payload.md` / `payload.xlsx` are **not** written here — "
        "back office uploads them via `POST /api/v1/jobs/ee/{job_id}/input-render`. "
        "`input_render_ready` is always false on this response until ops has uploaded. "
        "Customers and **back-office** accounts may create jobs (back office also has ops privileges). "
        "Requires sufficient EE token balance (`EE_JOB_SUBMIT_TOKEN_COST`, default 1); otherwise **402**."
    ),
)
def submit_express_estimate(
    payload: Annotated[
        ExpressEstimatePayload,
        Body(
            openapi_examples={
                "minimal": {
                    "summary": "Required project fields only",
                    "value": {
                        "projectDetails": {
                            "insuredName": "Jane Doe",
                            "claimNumber": "CLM-001",
                        },
                    },
                },
                "with_sections": {
                    "summary": "Project + optional sections",
                    "value": {
                        "projectDetails": {
                            "insuredName": "Jane Doe",
                            "claimNumber": "CLM-001",
                            "street": "123 Main St",
                            "city": "Austin",
                            "zipCode": "78701",
                            "depreciationRange": "light",
                            "notes": "Optional note",
                        },
                        "exterior": {
                            "pressureWash": {"enabled": True, "perimeterFeet": "120"},
                        },
                        "rooms": [{"id": 1, "name": "Kitchen"}],
                    },
                },
            },
        ),
    ],
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeJobCreatedData]:
    try:
        stored = payload.model_dump(mode="json", exclude_unset=True, by_alias=True)
        job = create_ee_job_from_payload(db, user=user, payload=stored)
    except InsufficientTokensError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        ) from e
    except Exception:
        logger.exception("submit_express_estimate failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create EE job",
        ) from None

    return SuccessEnvelope(
        message="OK",
        data=EeJobCreatedData(
            job_id=job.id,
            status=job.status,
            input_render_ready=False,
        ),
    )


@router.post(
    "/jobs/ee/{job_id}/input-render",
    summary="[Back office] Upload readable payload.md and payload.xlsx to Storage",
    description=(
        "Renders wizard JSON to markdown and Excel, writing `payload.md` and `payload.xlsx` to the EE readable bucket. "
        "**403** unless `user_type` is `back_office`. May target any customer's job by `job_id`."
    ),
)
def ee_retry_input_render(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_back_office),
) -> SuccessEnvelope[EeJobDetail]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    try:
        store_readable_input(job)
    except Exception:
        logger.exception("EE input render retry failed job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not upload readable exports to Storage",
        ) from None
    has_input = input_render_exists(job)
    has_xlsx = input_render_excel_exists(job)
    return SuccessEnvelope(message="OK", data=_ee_job_detail(job, has_input_render=has_input, has_input_excel=has_xlsx))


@router.get(
    "/jobs/ee/{job_id}",
    summary="EE job detail",
)
def ee_job_detail(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeJobDetail]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    has_input = input_render_exists(job)
    has_xlsx = input_render_excel_exists(job)
    return SuccessEnvelope(message="OK", data=_ee_job_detail(job, has_input_render=has_input, has_input_excel=has_xlsx))


@router.get(
    "/jobs/ee/{job_id}/input-download",
    summary="[Back office] Signed download URL for readable payload (markdown or Excel)",
    description=(
        "Short-lived read URL for `payload.md` or `payload.xlsx`. "
        "`format` default `markdown`; also accepts `md`, `excel`, `xlsx`, `spreadsheet`, `sheet`. "
        "Legacy jobs with only markdown get Excel generated on first spreadsheet download. "
        "**403** unless `user_type` is `back_office`."
    ),
)
def ee_input_download(
    job_id: uuid.UUID,
    download_format: Annotated[
        str,
        Query(
            alias="format",
            description="markdown | md | excel | xlsx | spreadsheet | sheet",
        ),
    ] = "markdown",
    db: Session = Depends(get_db),
    user: User = Depends(require_back_office),
) -> SuccessEnvelope[EeJobDownloadData]:
    response_format = _coerce_input_download_format(download_format)
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    if not input_render_exists(job):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Readable input not available — POST /api/v1/jobs/ee/{job_id}/input-render first",
        )
    bucket = ee_readable_bucket()
    ttl = get_settings().storage_signed_download_ttl_seconds
    if response_format == "excel":
        try:
            ensure_readable_input_excel(job)
        except Exception:
            logger.exception("EE readable excel backfill failed job_id=%s", job_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not prepare Excel export",
            ) from None
        if not input_render_excel_exists(job):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Excel export not available after upload attempt",
            )
        key = build_readable_input_excel_key(job.user_id, job.id)
        filename = "payload.xlsx"
        fmt: Literal["markdown", "excel", "output"] = "excel"
    else:
        key = build_readable_input_key(job.user_id, job.id)
        filename = "payload.md"
        fmt = "markdown"
    try:
        url = create_signed_download_url(bucket, key, expires_in=ttl)
    except Exception:
        logger.exception("signed input download URL failed job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create signed download URL",
        ) from None
    return SuccessEnvelope(
        message="OK",
        data=EeJobDownloadData(url=url, expires_in=ttl, format=fmt, filename=filename),
    )


@router.get(
    "/jobs/ee/{job_id}/output/download",
    summary="Signed download URL for operator-uploaded output file",
)
def ee_output_download(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeJobDownloadData]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    de = job.details_ee
    out_key = (de.output_file_key or "").strip() if de else ""
    if not out_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No output file yet — upload via presign flow then confirm",
        )
    bucket = ee_output_bucket()
    ttl = get_settings().storage_signed_download_ttl_seconds
    try:
        url = create_signed_download_url(bucket, out_key, expires_in=ttl)
    except Exception:
        logger.exception("signed output download URL failed job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create signed download URL",
        ) from None
    base = os.path.basename(out_key) or "output"
    return SuccessEnvelope(
        message="OK",
        data=EeJobDownloadData(url=url, expires_in=ttl, format="output", filename=base),
    )


@router.post(
    "/jobs/ee/{job_id}/output/upload-url",
    summary="Presigned upload URL for final output artifact",
)
def ee_output_upload_url(
    job_id: uuid.UUID,
    body: EeOutputUploadUrlBody,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeOutputUploadUrlData]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    if job.status == JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job already completed — reopen before replacing output",
        )
    try:
        out = issue_output_upload_url(job=job, filename=body.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    return SuccessEnvelope(
        message="OK",
        data=EeOutputUploadUrlData(
            upload_url=out["upload_url"],
            object_path=out["object_path"],
            token=out.get("token"),
        ),
    )


@router.post(
    "/jobs/ee/{job_id}/output/confirm",
    summary="Confirm output file landed in Storage",
)
def ee_output_confirm(
    job_id: uuid.UUID,
    body: EeOutputConfirmBody,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeJobDetail]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    if job.status == JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job already completed",
        )
    try:
        confirm_output_upload(db, job=job, object_path=body.object_path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    db.refresh(job)
    has_input = input_render_exists(job)
    has_xlsx = input_render_excel_exists(job)
    return SuccessEnvelope(message="OK", data=_ee_job_detail(job, has_input_render=has_input, has_input_excel=has_xlsx))


@router.post(
    "/jobs/ee/{job_id}/complete",
    summary="[Back office] Mark EE job completed (checkmark)",
    description=(
        "Sets status to `completed` and `completed_at`. **403** unless `user_type` is `back_office`. "
        "Requires output file confirmed first."
    ),
)
def ee_job_complete(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_back_office),
) -> SuccessEnvelope[EeJobDetail]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already completed")
    de = job.details_ee
    if de is None or not (de.output_file_key or "").strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload and confirm output before completing",
        )
    now = datetime.now(timezone.utc)
    prev = job.status
    job.status = JobStatus.COMPLETED
    job.completed_at = now
    db.add(
        JobStatusHistory(
            job_id=job.id,
            from_status=prev,
            to_status=JobStatus.COMPLETED,
            note="manual completion",
        )
    )
    db.commit()
    db.refresh(job)
    has_input = input_render_exists(job)
    has_xlsx = input_render_excel_exists(job)
    return SuccessEnvelope(message="OK", data=_ee_job_detail(job, has_input_render=has_input, has_input_excel=has_xlsx))


@router.post(
    "/jobs/ee/{job_id}/reopen",
    summary="[Back office] Undo completion (completed → confirmed)",
    description="**403** unless `user_type` is `back_office`.",
)
def ee_job_reopen(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_back_office),
) -> SuccessEnvelope[EeJobDetail]:
    job = _get_ee_job(db, user, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EE job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not completed",
        )
    prev = job.status
    job.status = JobStatus.CONFIRMED
    job.completed_at = None
    db.add(
        JobStatusHistory(
            job_id=job.id,
            from_status=prev,
            to_status=JobStatus.CONFIRMED,
            note="reopened",
        )
    )
    db.commit()
    db.refresh(job)
    has_input = input_render_exists(job)
    has_xlsx = input_render_excel_exists(job)
    return SuccessEnvelope(message="OK", data=_ee_job_detail(job, has_input_render=has_input, has_input_excel=has_xlsx))
