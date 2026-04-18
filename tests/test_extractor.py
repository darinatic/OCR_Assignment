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

    def test_prompt_includes_all_fields(self) -> None:
        """Test prompt includes all extraction fields."""
        prompt = build_extraction_prompt()

        # Referral letter fields
        assert "claimant_name" in prompt
        assert "provider_name" in prompt
        assert "signature_presence" in prompt
        assert "total_amount_paid" in prompt

        # Medical certificate fields
        assert "mc_days" in prompt
        assert "date_of_mc" in prompt
        assert "diagnosis_name" in prompt

        # Receipt fields
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

    @pytest.mark.parametrize("response,expected_type", [
        ('{"document_type": "receipt", "fields": {"total_amount": 100}}', "receipt"),
        ('{"document_type": "referral_letter", "fields": {}}', "referral_letter"),
    ])
    def test_parse_raw_json(self, response: str, expected_type: str) -> None:
        """Test parsing raw JSON response."""
        result = parse_claude_response(response)
        assert result["document_type"] == expected_type

    def test_parse_json_in_markdown_block(self) -> None:
        """Test parsing JSON in markdown code block."""
        response = """Here is the extracted data:

```json
{
  "document_type": "medical_certificate",
  "fields": {"claimant_name": "John Doe", "mc_days": 3}
}
```

The document appears to be a medical certificate."""

        result = parse_claude_response(response)

        assert result["document_type"] == "medical_certificate"
        assert result["fields"]["claimant_name"] == "John Doe"

    def test_parse_json_with_null_values(self) -> None:
        """Test parsing JSON with null values."""
        response = '{"document_type": "receipt", "fields": {"total_amount": null}}'
        result = parse_claude_response(response)
        assert result["fields"]["total_amount"] is None

    def test_invalid_json_raises_error(self) -> None:
        """Test invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_claude_response("This is not JSON at all")


# Integration tests - require ANTHROPIC_API_KEY
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestExtractDocumentDataIntegration:
    """Integration tests for extract_document_data (requires API key)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("pdf_name,expected_type", [
        ("referral_letter.pdf", "referral_letter"),
        ("medical_certificate.pdf", "medical_certificate"),
        ("receipt.pdf", "receipt"),
    ])
    async def test_extract_document(self, pdf_name: str, expected_type: str) -> None:
        """Test extraction from different document types."""
        pdf_path = SAMPLES_DIR / pdf_name
        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert "document_type" in result
        assert "fields" in result
        assert result["document_type"] == expected_type

    @pytest.mark.asyncio
    async def test_extract_unsupported_document_returns_other(self) -> None:
        """Test unsupported document (health screening) is classified as 'other'."""
        pdf_path = SAMPLES_DIR / "unsupported.pdf"
        if not pdf_path.exists():
            pytest.skip("unsupported.pdf not available")

        pdf_bytes = pdf_path.read_bytes()
        images = await convert_pdf_to_images(pdf_bytes)

        result = await extract_document_data(images)

        assert result["document_type"] == "other"
        assert result["fields"] == {}
