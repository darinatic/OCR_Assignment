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


class TestDocumentFields:
    """Tests for document field models."""

    def test_referral_letter_full_data(self) -> None:
        """Test ReferralLetterFields with all fields populated."""
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

    def test_referral_letter_defaults(self) -> None:
        """Test ReferralLetterFields defaults to None/False."""
        fields = ReferralLetterFields()
        assert fields.claimant_name is None
        assert fields.signature_presence is False
        assert fields.total_amount_paid is None

    def test_medical_certificate_full_data(self) -> None:
        """Test MedicalCertificateFields with all fields populated."""
        fields = MedicalCertificateFields(
            claimant_name="John Doe",
            claimant_address="123 Main St",
            diagnosis_name="Common Cold",
            icd_code="J00",
            mc_days=3,
        )
        assert fields.claimant_name == "John Doe"
        assert fields.mc_days == 3
        assert fields.icd_code == "J00"

    def test_medical_certificate_defaults(self) -> None:
        """Test MedicalCertificateFields defaults to None."""
        fields = MedicalCertificateFields()
        assert fields.claimant_name is None
        assert fields.mc_days is None

    def test_receipt_full_data(self) -> None:
        """Test ReceiptFields with all fields populated."""
        fields = ReceiptFields(
            claimant_name="John Doe",
            claimant_address="456 Oak Ave",
            provider_name="Medical Center",
            tax_amount=50,
            total_amount=550,
        )
        assert fields.claimant_name == "John Doe"
        assert fields.tax_amount == 50
        assert fields.total_amount == 550

    def test_receipt_defaults(self) -> None:
        """Test ReceiptFields defaults to None."""
        fields = ReceiptFields()
        assert fields.claimant_name is None
        assert fields.total_amount is None


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    @pytest.mark.parametrize("doc_type,model_class", [
        ("referral_letter", ReferralLetterFields),
        ("medical_certificate", MedicalCertificateFields),
        ("receipt", ReceiptFields),
    ])
    def test_extraction_result_types(self, doc_type: str, model_class) -> None:
        """Test extraction result for different document types."""
        result = ExtractionResult(
            document_type=doc_type,
            total_time=2.5,
            finalJson=model_class(),
        )
        assert result.document_type == doc_type
        assert result.total_time == 2.5


class TestResponses:
    """Tests for response models."""

    def test_ocr_response_structure(self) -> None:
        """Test OCRResponse structure and default message."""
        response = OCRResponse(
            result=ExtractionResult(
                document_type="referral_letter",
                total_time=2.0,
                finalJson=ReferralLetterFields(),
            ),
        )
        assert response.message == "Processing completed."
        assert response.result.document_type == "referral_letter"

    @pytest.mark.parametrize("error_type", [
        "file_missing",
        "unsupported_document_type",
        "internal_server_error",
    ])
    def test_error_responses(self, error_type: str) -> None:
        """Test error response types."""
        error = ErrorResponse(error=error_type)
        assert error.error == error_type
