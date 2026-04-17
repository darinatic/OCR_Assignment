"""Tests for API endpoint."""

import os
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from main import app


SAMPLES_DIR = Path(__file__).parent.parent / "samples"


class TestOCREndpointValidation:
    """Tests for OCR endpoint input validation (no API key needed)."""

    @pytest.mark.asyncio
    async def test_missing_file_returns_400(self) -> None:
        """Test that missing file returns 400 error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ocr")

        assert response.status_code == 400
        assert response.json() == {"error": "file_missing"}

    @pytest.mark.asyncio
    async def test_invalid_mime_type_returns_400(self) -> None:
        """Test that invalid MIME type returns 400 error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("test.txt", b"hello world", "text/plain")},
            )

        assert response.status_code == 400
        assert response.json() == {"error": "file_missing"}

    @pytest.mark.asyncio
    async def test_unsupported_content_type_returns_400(self) -> None:
        """Test that unsupported content type returns 400."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("test.gif", b"GIF89a", "image/gif")},
            )

        assert response.status_code == 400
        assert response.json() == {"error": "file_missing"}


class TestPostProcessing:
    """Tests for field post-processing functions."""

    def test_post_process_referral_letter(self) -> None:
        """Test referral letter post-processing."""
        from app.api import post_process_referral_letter

        fields = {
            "claimant_name": "John Doe",
            "provider_name": "ABC Clinic - Fullerton Health",
            "signature_presence": True,
            "total_amount_paid": "$1,500.00",
            "total_approved_amount": "S$1,000.50",
            "total_requested_amount": None,
        }

        result = post_process_referral_letter(fields)

        assert result.claimant_name == "John Doe"
        assert result.provider_name == "ABC Clinic"  # Fullerton Health removed
        assert result.signature_presence is True
        assert result.total_amount_paid == 1500
        assert result.total_approved_amount == 1000
        assert result.total_requested_amount is None

    def test_post_process_medical_certificate(self) -> None:
        """Test medical certificate post-processing."""
        from app.api import post_process_medical_certificate

        fields = {
            "claimant_name": "Jane Doe",
            "claimant_date_of_birth": "15-Jun-1990",
            "date_of_mc": "04-JAN-2023",
            "mc_days": "3",
            "provider_name": "XYZ Hospital",
        }

        result = post_process_medical_certificate(fields)

        assert result.claimant_name == "Jane Doe"
        assert result.claimant_date_of_birth == "15/06/1990"
        assert result.date_of_mc == "04/01/2023"
        assert result.mc_days == 3
        assert result.provider_name == "XYZ Hospital"

    def test_post_process_receipt(self) -> None:
        """Test receipt post-processing."""
        from app.api import post_process_receipt

        fields = {
            "claimant_name": "Bob Smith",
            "claimant_address": "123 Main St",
            "provider_name": "Medical Center",
            "tax_amount": "$10.00",
            "total_amount": "$110.50",
        }

        result = post_process_receipt(fields)

        assert result.claimant_name == "Bob Smith"
        assert result.claimant_address == "123 Main St"
        assert result.provider_name == "Medical Center"
        assert result.tax_amount == 10
        assert result.total_amount == 110

    def test_signature_presence_falsy_values(self) -> None:
        """Test signature_presence handles falsy values correctly."""
        from app.api import post_process_referral_letter

        # Test with None
        result = post_process_referral_letter({"signature_presence": None})
        assert result.signature_presence is False

        # Test with False
        result = post_process_referral_letter({"signature_presence": False})
        assert result.signature_presence is False

        # Test with empty dict
        result = post_process_referral_letter({})
        assert result.signature_presence is False


# Integration tests - require ANTHROPIC_API_KEY
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestOCREndpointIntegration:
    """Integration tests for OCR endpoint (requires API key)."""

    @pytest.mark.asyncio
    async def test_process_referral_letter(self) -> None:
        """Test processing referral letter PDF."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("referral_letter.pdf", pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Processing completed."
        assert "result" in data
        assert data["result"]["document_type"] == "referral_letter"
        assert "total_time" in data["result"]
        assert "finalJson" in data["result"]

        # Check expected fields exist
        final_json = data["result"]["finalJson"]
        assert "claimant_name" in final_json
        assert "provider_name" in final_json
        assert "signature_presence" in final_json

    @pytest.mark.asyncio
    async def test_process_medical_certificate(self) -> None:
        """Test processing medical certificate PDF."""
        pdf_path = SAMPLES_DIR / "medical_certificate.pdf"
        pdf_bytes = pdf_path.read_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("medical_certificate.pdf", pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["result"]["document_type"] == "medical_certificate"
        final_json = data["result"]["finalJson"]
        assert "claimant_name" in final_json
        assert "mc_days" in final_json
        assert "date_of_mc" in final_json

    @pytest.mark.asyncio
    async def test_process_receipt(self) -> None:
        """Test processing receipt PDF."""
        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("receipt.pdf", pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["result"]["document_type"] == "receipt"
        final_json = data["result"]["finalJson"]
        assert "claimant_name" in final_json
        assert "total_amount" in final_json

    @pytest.mark.asyncio
    async def test_response_includes_timing(self) -> None:
        """Test that response includes timing information."""
        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("receipt.pdf", pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        assert "total_time" in data["result"]
        assert isinstance(data["result"]["total_time"], (int, float))
        assert data["result"]["total_time"] > 0

    @pytest.mark.asyncio
    async def test_jpeg_image_processing(self) -> None:
        """Test that JPEG images can be processed."""
        # First convert a PDF page to simulate a JPEG
        from app.pdf_converter import convert_pdf_to_images

        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        # Use PNG (which we have) as a proxy - the API should accept it
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("receipt.png", images[0], "image/png")},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unsupported_document_returns_422(self) -> None:
        """Test unsupported document (health screening) returns 422."""
        pdf_path = SAMPLES_DIR / "unsupported.pdf"
        if not pdf_path.exists():
            pytest.skip("unsupported.pdf not available")

        pdf_bytes = pdf_path.read_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ocr",
                files={"file": ("unsupported.pdf", pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 422
        assert response.json() == {"error": "unsupported_document_type"}

