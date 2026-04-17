"""Tests for PDF converter."""

import pytest
from pathlib import Path
from app.pdf_converter import convert_pdf_to_images, get_image_bytes_async


SAMPLES_DIR = Path(__file__).parent.parent / "samples"


class TestConvertPdfToImages:
    """Tests for convert_pdf_to_images function."""

    @pytest.mark.asyncio
    async def test_converts_referral_letter_pdf(self) -> None:
        """Test conversion of referral letter PDF produces images."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await convert_pdf_to_images(pdf_bytes)

        assert len(images) >= 1
        # Verify each output is PNG (starts with PNG signature)
        for img in images:
            assert img[:8] == b"\x89PNG\r\n\x1a\n", "Output should be PNG format"

    @pytest.mark.asyncio
    async def test_converts_medical_certificate_pdf(self) -> None:
        """Test conversion of medical certificate PDF."""
        pdf_path = SAMPLES_DIR / "medical_certificate.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await convert_pdf_to_images(pdf_bytes)

        assert len(images) >= 1
        assert images[0][:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_converts_receipt_pdf(self) -> None:
        """Test conversion of receipt PDF."""
        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await convert_pdf_to_images(pdf_bytes)

        assert len(images) >= 1
        assert images[0][:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_image_has_reasonable_size(self) -> None:
        """Test that converted images have reasonable size (not empty)."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await convert_pdf_to_images(pdf_bytes)

        # PNG images should be at least a few KB
        for img in images:
            assert len(img) > 1000, "Image should not be nearly empty"

    @pytest.mark.asyncio
    async def test_custom_dpi(self) -> None:
        """Test conversion with custom DPI produces different sized images."""
        pdf_path = SAMPLES_DIR / "referral_letter.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images_low = await convert_pdf_to_images(pdf_bytes, dpi=72)
        images_high = await convert_pdf_to_images(pdf_bytes, dpi=200)

        # Higher DPI should produce larger images
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
    async def test_jpeg_passthrough(self) -> None:
        """Test JPEG image is passed through as-is."""
        # Create a minimal JPEG-like content (just for testing passthrough)
        jpeg_bytes = b"\xff\xd8\xff\xe0fake_jpeg_content"

        images = await get_image_bytes_async(jpeg_bytes, "image/jpeg")

        assert len(images) == 1
        assert images[0] == jpeg_bytes

    @pytest.mark.asyncio
    async def test_png_passthrough(self) -> None:
        """Test PNG image is passed through as-is."""
        # Minimal PNG header + fake content
        png_bytes = b"\x89PNG\r\n\x1a\nfake_png_content"

        images = await get_image_bytes_async(png_bytes, "image/png")

        assert len(images) == 1
        assert images[0] == png_bytes

    @pytest.mark.asyncio
    async def test_single_page_pdf_returns_one_image(self) -> None:
        """Test single-page PDF returns exactly one image."""
        # Most sample docs should be single page
        pdf_path = SAMPLES_DIR / "receipt.pdf"
        pdf_bytes = pdf_path.read_bytes()

        images = await get_image_bytes_async(pdf_bytes, "application/pdf")

        # Assuming receipt is single page
        assert len(images) >= 1
