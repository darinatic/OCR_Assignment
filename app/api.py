"""API endpoint for OCR document processing."""

import logging
import time
from typing import Any

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.models import (
    ReferralLetterFields,
    MedicalCertificateFields,
    ReceiptFields,
    ExtractionResult,
    OCRResponse,
    ErrorResponse,
)
from app.pdf_converter import get_image_bytes_async
from app.extractor import extract_document_data
from app.utils import normalize_amount, format_date, clean_provider_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
SUPPORTED_DOCUMENT_TYPES = {"referral_letter", "medical_certificate", "receipt"}


def post_process_referral_letter(fields: dict[str, Any]) -> ReferralLetterFields:
    """Apply normalization rules to referral letter fields."""
    return ReferralLetterFields(
        claimant_name=fields.get("claimant_name"),
        provider_name=clean_provider_name(fields.get("provider_name")),
        signature_presence=bool(fields.get("signature_presence", False)),
        total_amount_paid=normalize_amount(fields.get("total_amount_paid")),
        total_approved_amount=normalize_amount(fields.get("total_approved_amount")),
        total_requested_amount=normalize_amount(fields.get("total_requested_amount")),
    )


def post_process_medical_certificate(fields: dict[str, Any]) -> MedicalCertificateFields:
    """Apply normalization rules to medical certificate fields."""
    mc_days = fields.get("mc_days")
    if mc_days is not None:
        try:
            mc_days = int(mc_days)
        except (ValueError, TypeError):
            mc_days = None

    return MedicalCertificateFields(
        claimant_name=fields.get("claimant_name"),
        claimant_address=fields.get("claimant_address"),
        claimant_date_of_birth=format_date(fields.get("claimant_date_of_birth")),
        diagnosis_name=fields.get("diagnosis_name"),
        discharge_date_time=format_date(fields.get("discharge_date_time")),
        icd_code=fields.get("icd_code"),
        provider_name=clean_provider_name(fields.get("provider_name")),
        submission_date_time=format_date(fields.get("submission_date_time")),
        date_of_mc=format_date(fields.get("date_of_mc")),
        mc_days=mc_days,
    )


def post_process_receipt(fields: dict[str, Any]) -> ReceiptFields:
    """Apply normalization rules to receipt fields."""
    return ReceiptFields(
        claimant_name=fields.get("claimant_name"),
        claimant_address=fields.get("claimant_address"),
        claimant_date_of_birth=format_date(fields.get("claimant_date_of_birth")),
        provider_name=clean_provider_name(fields.get("provider_name")),
        tax_amount=normalize_amount(fields.get("tax_amount")),
        total_amount=normalize_amount(fields.get("total_amount")),
    )


@router.post(
    "/ocr",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Missing or invalid file"},
        422: {"model": ErrorResponse, "description": "Unsupported document type"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def process_document(file: UploadFile = File(default=None)) -> OCRResponse:
    """
    Process a medical document and extract structured data.

    Accepts PDF, JPEG, or PNG files. Returns extracted fields based on
    detected document type (referral_letter, medical_certificate, or receipt).
    """
    start_time = time.time()

    if file is None or file.filename == "":
        logger.warning("Request received without file")
        return JSONResponse(status_code=400, content={"error": "file_missing"})

    content_type = file.content_type
    if content_type not in SUPPORTED_MIME_TYPES:
        logger.warning(f"Unsupported file type: {content_type}")
        return JSONResponse(status_code=400, content={"error": "file_missing"})

    logger.info(f"Processing file: {file.filename}, type: {content_type}, size: {file.size}")

    try:
        content = await file.read()
        images = await get_image_bytes_async(content, content_type)
        logger.info(f"Converted to {len(images)} image(s)")

        api_start = time.time()
        extraction_result = await extract_document_data(images)
        logger.info(f"Claude API call took {time.time() - api_start:.2f}s")

        document_type = extraction_result.get("document_type")
        if document_type not in SUPPORTED_DOCUMENT_TYPES:
            logger.warning(f"Unsupported document type: {document_type}")
            return JSONResponse(status_code=422, content={"error": "unsupported_document_type"})

        fields = extraction_result.get("fields", {})
        logger.info(f"Extracted fields: {fields}")

        if document_type == "referral_letter":
            final_json = post_process_referral_letter(fields)
        elif document_type == "medical_certificate":
            final_json = post_process_medical_certificate(fields)
        else:
            final_json = post_process_receipt(fields)

        total_time = round(time.time() - start_time, 2)
        logger.info(f"Total processing time: {total_time}s")

        return OCRResponse(
            message="Processing completed.",
            result=ExtractionResult(
                document_type=document_type,
                total_time=total_time,
                finalJson=final_json,
            ),
        )

    except ValueError as e:
        logger.error(f"Value error during processing: {e}")
        return JSONResponse(status_code=500, content={"error": "internal_server_error"})
    except Exception as e:
        logger.exception(f"Unexpected error during processing: {e}")
        return JSONResponse(status_code=500, content={"error": "internal_server_error"})
