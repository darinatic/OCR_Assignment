"""Tests for Pydantic models."""

import pytest
from app.models import (
    ReferralLetterFields,
    MedicalCertificateFields,
    ReceiptFields,
    ExtractionResult,
    OCRResponse,
    ErrorResponse,
)


class TestReferralLetterFields:
    """Tests for ReferralLetterFields model."""

    def test_valid_full_data(self) -> None:
        """Test with all fields populated."""
        fields = ReferralLetterFields(
            claimant_name="John Doe",
            provider_name="ABC Clinic",
            signature_presence=True,
            total_amount_paid=3000000,
            total_approved_amount=3000000,
            total_requested_amount=3000000,
        )
        assert fields.claimant_name == "John Doe"
        assert fields.provider_name == "ABC Clinic"
        assert fields.signature_presence is True
        assert fields.total_amount_paid == 3000000

    def test_nullable_fields(self) -> None:
        """Test that fields default to None/False."""
        fields = ReferralLetterFields()
        assert fields.claimant_name is None
        assert fields.provider_name is None
        assert fields.signature_presence is False
        assert fields.total_amount_paid is None
        assert fields.total_approved_amount is None
        assert fields.total_requested_amount is None

    def test_partial_data(self) -> None:
        """Test with only some fields populated."""
        fields = ReferralLetterFields(
            claimant_name="Jane Doe",
            signature_presence=True,
        )
        assert fields.claimant_name == "Jane Doe"
        assert fields.signature_presence is True
        assert fields.provider_name is None


class TestMedicalCertificateFields:
    """Tests for MedicalCertificateFields model."""

    def test_valid_full_data(self) -> None:
        """Test with all fields populated."""
        fields = MedicalCertificateFields(
            claimant_name="John Doe",
            claimant_address="123 Main St",
            claimant_date_of_birth="01/01/1990",
            diagnosis_name="Common Cold",
            discharge_date_time="15/01/2025",
            icd_code="J00",
            provider_name="XYZ Hospital",
            submission_date_time="10/01/2025",
            date_of_mc="10/01/2025",
            mc_days=3,
        )
        assert fields.claimant_name == "John Doe"
        assert fields.mc_days == 3
        assert fields.icd_code == "J00"

    def test_nullable_fields(self) -> None:
        """Test that all fields default to None."""
        fields = MedicalCertificateFields()
        assert fields.claimant_name is None
        assert fields.claimant_address is None
        assert fields.claimant_date_of_birth is None
        assert fields.diagnosis_name is None
        assert fields.discharge_date_time is None
        assert fields.icd_code is None
        assert fields.provider_name is None
        assert fields.submission_date_time is None
        assert fields.date_of_mc is None
        assert fields.mc_days is None

    def test_mc_days_integer(self) -> None:
        """Test mc_days accepts integer."""
        fields = MedicalCertificateFields(mc_days=5)
        assert fields.mc_days == 5
        assert isinstance(fields.mc_days, int)


class TestReceiptFields:
    """Tests for ReceiptFields model."""

    def test_valid_full_data(self) -> None:
        """Test with all fields populated."""
        fields = ReceiptFields(
            claimant_name="John Doe",
            claimant_address="456 Oak Ave",
            claimant_date_of_birth="15/06/1985",
            provider_name="Medical Center",
            tax_amount=50,
            total_amount=550,
        )
        assert fields.claimant_name == "John Doe"
        assert fields.tax_amount == 50
        assert fields.total_amount == 550

    def test_nullable_fields(self) -> None:
        """Test that all fields default to None."""
        fields = ReceiptFields()
        assert fields.claimant_name is None
        assert fields.claimant_address is None
        assert fields.claimant_date_of_birth is None
        assert fields.provider_name is None
        assert fields.tax_amount is None
        assert fields.total_amount is None

    def test_amount_fields_integer(self) -> None:
        """Test amount fields accept integers."""
        fields = ReceiptFields(tax_amount=100, total_amount=1000)
        assert fields.tax_amount == 100
        assert fields.total_amount == 1000
        assert isinstance(fields.tax_amount, int)
        assert isinstance(fields.total_amount, int)


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_referral_letter_result(self) -> None:
        """Test extraction result for referral letter."""
        result = ExtractionResult(
            document_type="referral_letter",
            total_time=2.5,
            finalJson=ReferralLetterFields(claimant_name="Test"),
        )
        assert result.document_type == "referral_letter"
        assert result.total_time == 2.5
        assert result.finalJson.claimant_name == "Test"

    def test_medical_certificate_result(self) -> None:
        """Test extraction result for medical certificate."""
        result = ExtractionResult(
            document_type="medical_certificate",
            total_time=3.0,
            finalJson=MedicalCertificateFields(mc_days=2),
        )
        assert result.document_type == "medical_certificate"
        assert result.finalJson.mc_days == 2

    def test_receipt_result(self) -> None:
        """Test extraction result for receipt."""
        result = ExtractionResult(
            document_type="receipt",
            total_time=1.5,
            finalJson=ReceiptFields(total_amount=500),
        )
        assert result.document_type == "receipt"
        assert result.finalJson.total_amount == 500


class TestOCRResponse:
    """Tests for OCRResponse model."""

    def test_success_response(self) -> None:
        """Test successful OCR response structure."""
        response = OCRResponse(
            message="Processing completed.",
            result=ExtractionResult(
                document_type="referral_letter",
                total_time=2.0,
                finalJson=ReferralLetterFields(),
            ),
        )
        assert response.message == "Processing completed."
        assert response.result.document_type == "referral_letter"

    def test_default_message(self) -> None:
        """Test default message value."""
        response = OCRResponse(
            result=ExtractionResult(
                document_type="receipt",
                total_time=1.0,
                finalJson=ReceiptFields(),
            ),
        )
        assert response.message == "Processing completed."


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_file_missing_error(self) -> None:
        """Test file missing error."""
        error = ErrorResponse(error="file_missing")
        assert error.error == "file_missing"

    def test_unsupported_document_error(self) -> None:
        """Test unsupported document type error."""
        error = ErrorResponse(error="unsupported_document_type")
        assert error.error == "unsupported_document_type"

    def test_internal_server_error(self) -> None:
        """Test internal server error."""
        error = ErrorResponse(error="internal_server_error")
        assert error.error == "internal_server_error"
