"""PDF to image conversion using PyMuPDF."""

import fitz


async def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 300) -> list[bytes]:
    """Convert PDF bytes to a list of PNG image bytes, one per page."""
    images: list[bytes] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pixmap = page.get_pixmap(matrix=matrix)
            images.append(pixmap.tobytes("png"))
    finally:
        doc.close()

    return images


def get_image_bytes(content: bytes, content_type: str) -> list[bytes]:
    """
    Get image bytes from file content.

    For PDFs, converts each page to PNG. For images, returns as-is.
    """
    if content_type == "application/pdf":
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(convert_pdf_to_images(content))
        finally:
            loop.close()
    else:
        return [content]


async def get_image_bytes_async(content: bytes, content_type: str) -> list[bytes]:
    """Async version of get_image_bytes."""
    if content_type == "application/pdf":
        return await convert_pdf_to_images(content)
    else:
        return [content]
