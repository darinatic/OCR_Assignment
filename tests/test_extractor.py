"""Tests for Claude Vision extractor."""

import os
import pytest
from pathlib import Path
from app.extractor import build_extraction_prompt, parse_claude_response, extract_document_data
from app.pdf_converter import convert_pdf_to_images


SAMPLES_DIR = Path(__file__).parent.parent / "samples"


class TestBuildExtractionPrompt:
    """Tests for build_extraction_prompt function."""

    def test_prompt_includes_document_types(self) -> None:
        """Test prompt includes all document types."""
        prompt = build_extraction_prompt()

        assert "referral_letter" in prompt
        assert "medical_certificate" in prompt
        assert "receipt" in prompt
        assert "other" in prompt

    def test_prompt_includes_other_category(self) -> None:
        """Test prompt includes 'other' document category."""
        prompt = build_extraction_prompt()

        assert "other" in prompt.lower()
        assert "don't fit" in prompt.lower() or "doesn't fit" in prompt.lower()

    def test_prompt_includes_referral_fields(self) -> None:
        """Test prompt includes referral letter fields."""
        prompt = build_extraction_prompt()

        assert "claimant_name" in prompt
        assert "provider_name" in prompt
        assert "signature_presence" in prompt
        assert "total_amount_paid" in prompt
        assert "total_approved_amount" in prompt
        assert "total_requested_amount" in prompt

    def test_prompt_includes_medical_certificate_fields(self) -> None:
        """Test prompt includes medical certificate fields."""
        prompt = build_extraction_prompt()

        assert "claimant_address" in prompt
        assert "claimant_date_of_birth" in prompt
        assert "diagnosis_name" in prompt
        assert "discharge_date_time" in prompt
        assert "icd_code" in prompt
        assert "submission_date_time" in prompt
        assert "date_of_mc" in prompt
        assert "mc_days" in prompt

    def test_prompt_includes_receipt_fields(self) -> None:
        """Test prompt includes receipt fields."""
        prompt = build_extraction_prompt()

        assert "tax_amount" in prompt
        assert "total_amount" in prompt

    def test_prompt_mentions_fullerton_health_exclusion(self) -> None:
        """Test prompt instructs to exclude Fullerton Health."""
        prompt = build_extraction_prompt()

        assert "Fullerton Health" in prompt

    def test_prompt_requests_json_output(self) -> None:
        """Test prompt requests JSON output."""
        prompt = build_extraction_prompt()

        assert "JSON" in prompt
        assert "document_type" in prompt


class TestParseClaudeResponse:
    """Tests for parse_claude_response function."""

    def test_parse_raw_json(self) -> None:
        """Test parsing raw JSON response."""
        response = '{"document_type": "receipt", "fields": {"total_amount": 100}}'
        result = parse_claude_response(response)

        assert result["document_type"] == "receipt"
        assert result["fields"]["total_amount"] == 100

    def test_parse_json_in_markdown_block(self) -> None:
        """Test parsing JSON in markdown code block."""
        response = """Here is the extracted data:

```json
{
  "document_type": "medical_certificate",
  "fields": {
    "claimant_name": "John Doe",
    "mc_days": 3
  }
}
```

The document appears to be a medical certificate."""

        result = parse_claude_response(response)

        assert result["document_type"] == "medical_certificate"
        assert result["fields"]["claimant_name"] == "John Doe"
        assert result["fields"]["mc_days"] == 3

    def test_parse_json_in_code_block_without_language(self) -> None:
        """Test parsing JSON in code block without language specifier."""
        response = """```
{"document_type": "referral_letter", "fields": {}}
```"""

        result = parse_claude_response(response)
        assert result["document_type"] == "referral_letter"

    def test_parse_json_with_surrounding_text(self) -> None:
        """Test parsing JSON surrounded by text."""
        response = """The analysis shows:
{"document_type": "receipt", "fields": {"total_amount": 50}}
Based on the content..."""

        result = parse_claude_response(response)
        assert result["document_type"] == "receipt"

    def test_parse_json_with_null_values(self) -> None:
        """Test parsing JSON with null values."""
        response = '{"document_type": "receipt", "fields": {"total_amount": null}}'
        result = parse_claude_response(response)

        assert result["fields"]["total_amount"] is None

    def test_invalid_json_raises_error(self) -> None:
        """Test invalid JSON raises ValueError."""
        response = "This is not JSON at all"

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_claude_response(response)

    def test_parse_with_whitespace(self) -> None:
        """Test parsing JSON with extra whitespace."""
        response = """

  {"document_type": "receipt", "fields": {}}

"""
        result = parse_claude_response(response)
        assert result["document_type"] == "receipt"


# Integration tests - require ANTHROPIC_API_KEY
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestExtractDocumentDataIntegration:
    """Integration tests for extract_document_data (requires API key)."""

    @pytest.mark.asyncio
    async def test_extract_referral_letter(self) -> None:
        """Test extraction from referral letter PDF."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert "fields" in result
        assert result["document_type"] == "referral_letter"

    @pytest.mark.asyncio
    async def test_extract_medical_certificate(self) -> None:
        """Test extraction from medical certificate PDF."""
        pdf_path = SAMPLES_DIR / "medical_certificate.pdf"
        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert result["document_type"] == "medical_certificate"

    @pytest.mark.asyncio
    async def test_extract_receipt(self) -> None:
        """Test extraction from receipt PDF."""
        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert result["document_type"] == "receipt"

    @pytest.mark.asyncio
    async def test_extract_unsupported_document_returns_other(self) -> None:
        """Test unsupported document (health screening) is classified as 'other'."""
        pdf_path = SAMPLES_DIR / "unsupported.pdf"
        if not pdf_path.exists():
            pytest.skip("unsupported.pdf not available")

        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert result["document_type"] == "other"
        assert result["fields"] == {}

    @pytest.mark.asyncio
    async def test_extract_blank_document_returns_other(self) -> None:
        """Test blank document is classified as 'other'."""
        pdf_path = SAMPLES_DIR / "blank.pdf"
        if not pdf_path.exists():
            pytest.skip("blank.pdf not available")

        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert result["document_type"] == "other"
        assert result["fields"] == {}
