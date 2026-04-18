"""Tests for PDF converter."""

import pytest
from pathlib import Path
from app.pdf_converter import convert_pdf_to_images, get_image_bytes_async


SAMPLES_DIR = Path(__file__).parent.parent / "samples"


class TestConvertPdfToImages:
    """Tests for convert_pdf_to_images function."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("pdf_name", [
        "referral_letter.pdf",
        "medical_certificate.pdf",
        "receipt.pdf",
    ])
    async def test_converts_pdf_to_png(self, pdf_name: str) -> None:
        """Test PDF conversion produces PNG images."""
        pdf_path = SAMPLES_DIR / pdf_name
        pdf_bytes = pdf_path.read_bytes()

        images = await convert_pdf_to_images(pdf_bytes)

        assert len(images) >= 1
        assert images[0][:8] == b"\x89PNG\r\n\x1a\n", "Output should be PNG format"
        assert len(images[0]) > 1000, "Image should not be nearly empty"

    @pytest.mark.asyncio
    async def test_custom_dpi(self) -> None:
        """Test conversion with different DPI produces different sized images."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images_low = await convert_pdf_to_images(pdf_bytes, dpi=72)
        images_high = await convert_pdf_to_images(pdf_bytes, dpi=200)

        assert len(images_high[0]) > len(images_low[0])


class TestGetImageBytesAsync:
    """Tests for get_image_bytes_async function."""

    @pytest.mark.asyncio
    async def test_pdf_returns_png_list(self) -> None:
        """Test PDF input returns list of PNG images."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await get_image_bytes_async(pdf_bytes, "application/pdf")

        assert isinstance(images, list)
        assert len(images) >= 1
        assert images[0][:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mime_type,content", [
        ("image/jpeg", b"\xff\xd8\xff\xe0fake_jpeg_content"),
        ("image/png", b"\x89PNG\r\n\x1a\nfake_png_content"),
    ])
    async def test_image_passthrough(self, mime_type: str, content: bytes) -> None:
        """Test JPEG/PNG images are passed through as-is."""
        images = await get_image_bytes_async(content, mime_type)

        assert len(images) == 1
        assert images[0] == content
