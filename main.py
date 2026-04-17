"""
OCR Document Processing Service

FastAPI microservice that accepts medical documents (PDF/images),
classifies them, and extracts structured data using Claude Vision API.
"""

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import router

load_dotenv()

app = FastAPI(
    title="OCR Document Processing Service",
    description="Classifies and extracts data from medical documents",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "ocr-document-processor"}
