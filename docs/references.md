# Technical References

Documentation notes gathered 2026-04-13 for OCR endpoint implementation.

## Claude Vision API

**Source**: [Claude Vision Docs](https://platform.claude.com/docs/en/build-with-claude/vision)

### Supported Formats
- Images: JPEG, PNG, GIF, WebP
- Max file size: 5 MB per image (API)
- Max dimensions: 8000x8000 px (1568px recommended for optimal performance)

### Token Calculation
```
tokens = (width_px * height_px) / 750
```
Example: 1000x1000 image = ~1,334 tokens

### Best Practices
- Place images BEFORE text queries in requests
- Ensure clarity and legible text
- Label multiple images (Image 1, Image 2) when comparing

## Claude PDF Support

**Source**: [Claude PDF Docs](https://platform.claude.com/docs/en/build-with-claude/pdf-support)

### Limitations
- Max request size: 32 MB
- Max pages: 100-600 (model dependent)
- Standard PDF only (no passwords/encryption)
- Dense PDFs can fill context before page limit

### Token Costs
- Text: 1,500-3,000 tokens per page
- Image: Additional vision-based cost per page

### Sending Methods
1. Base64-encoded in request body
2. URL reference to hosted PDF
3. Files API (upload once, reference by file_id)

## PyMuPDF (PDF → Image)

**Source**: [PyMuPDF Docs](https://pymupdf.readthedocs.io/en/latest/)

### Core Usage
```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[0]
pix = page.get_pixmap()  # Default ~72 DPI
pix.save("output.png")

# Higher resolution
pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x = ~144 DPI
pix.set_dpi(150, 150)
pix.save("output.png")
```

### Performance
- 3-5x faster than pdf2image
- No external dependencies (self-contained)
- Supports PNG, JPEG, PSD output

### Output Formats
| Format | Alpha | Notes |
|--------|-------|-------|
| PNG | Yes | Best for documents |
| JPEG | No | Smaller files, quality param |

## FastAPI File Uploads

**Source**: [FastAPI Docs](https://fastapi.tiangolo.com/tutorial/request-files/)

### Requirements
```bash
pip install python-multipart
```

### UploadFile Advantages
- Memory efficient (spooled to disk if large)
- Provides `filename`, `content_type` attributes
- Async methods: `read()`, `write()`, `seek()`, `close()`

### Basic Pattern
```python
from fastapi import FastAPI, UploadFile, HTTPException

@app.post("/ocr")
async def process_document(file: UploadFile):
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(400, detail="file_missing")

    content = await file.read()
    # Process...
```

### Validation Notes
- Check content_type for MIME validation
- Cannot mix File/Form with JSON Body parameters
- Forms with files use multipart/form-data encoding

## Anthropic Python SDK

**Source**: [anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)

### Installation
```bash
pip install anthropic
```

### Vision Request Pattern
```python
import anthropic
import base64

client = anthropic.Anthropic()

# Base64 image
with open("image.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            },
            {
                "type": "text",
                "text": "Extract the following fields..."
            }
        ]
    }]
)
```

### PDF Document Request
```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_base64
                }
            },
            {
                "type": "text",
                "text": "Classify and extract..."
            }
        ]
    }]
)
```

## Pydantic v2

### Model Definition
```python
from pydantic import BaseModel
from typing import Optional

class ReferralLetterFields(BaseModel):
    claimant_name: Optional[str] = None
    provider_name: Optional[str] = None
    signature_presence: bool = False
    total_amount_paid: Optional[int] = None
    total_approved_amount: Optional[int] = None
    total_requested_amount: Optional[int] = None
```

### Validation
- Use `Optional[T] = None` for nullable fields
- Use `model_validate()` or `model_validate_json()` for parsing
- `model_dump()` for serialization
