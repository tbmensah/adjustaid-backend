from enum import StrEnum


class UserType(StrEnum):
    """App role: customers submit jobs; back_office may submit and process any customer's EE job."""

    CUSTOMER = "customer"
    BACK_OFFICE = "back_office"


class TokenType(StrEnum):
    EE = "ee"
    FF = "ff"


class TransactionReason(StrEnum):
    PURCHASE = "purchase"
    JOB_DEDUCT = "job_deduct"
    REFUND = "refund"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class StripeStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class JobType(StrEnum):
    EE = "ee"
    FF = "ff"


class JobStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class FfPdfType(StrEnum):
    NFIP_PROOF_OF_LOSS = "NFIP_proof_of_loss"
    PRELIMINARY_REPORT = "preliminary_report"
    XACT_CONTENTS_EXPORT = "xact_contents_export"
    FLOOD_DAMAGE_ASSESSMENT = "flood_damage_assessment"
