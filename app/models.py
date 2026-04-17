"""Pydantic models for OCR document extraction."""

from typing import Literal, Union
from pydantic import BaseModel


# Document field models

class ReferralLetterFields(BaseModel):
    """Extracted fields from a referral letter."""

    claimant_name: str | None = None
    provider_name: str | None = None
    signature_presence: bool = False
    total_amount_paid: int | None = None
    total_approved_amount: int | None = None
    total_requested_amount: int | None = None


class MedicalCertificateFields(BaseModel):
    """Extracted fields from a medical certificate."""

    claimant_name: str | None = None
    claimant_address: str | None = None
    claimant_date_of_birth: str | None = None
    diagnosis_name: str | None = None
    discharge_date_time: str | None = None
    icd_code: str | None = None
    provider_name: str | None = None
    submission_date_time: str | None = None  # Admission datetime 
    date_of_mc: str | None = None
    mc_days: int | None = None


class ReceiptFields(BaseModel):
    """Extracted fields from a receipt."""

    claimant_name: str | None = None
    claimant_address: str | None = None
    claimant_date_of_birth: str | None = None
    provider_name: str | None = None
    tax_amount: int | None = None
    total_amount: int | None = None


# API response models

DocumentType = Literal["referral_letter", "medical_certificate", "receipt"]
FinalJson = Union[ReferralLetterFields, MedicalCertificateFields, ReceiptFields]


class ExtractionResult(BaseModel):
    """Result of document extraction."""

    document_type: DocumentType
    total_time: float
    finalJson: FinalJson


class OCRResponse(BaseModel):
    """Successful OCR processing response."""

    message: str = "Processing completed."
    result: ExtractionResult


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
