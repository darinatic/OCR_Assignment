"""Utility functions for OCR document processing."""

import re
from datetime import datetime


def normalize_amount(value: str | None) -> int | None:
    """
    Convert monetary string to integer by removing currency symbols,
    thousand separators, and truncating decimals.

    Examples:
        "$3,000,000.00" → 3000000
        "S$49.25" → 49
        "3.65" → 3
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"^[A-Z]{0,3}\$\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(SGD|USD|MYR|EUR|GBP)\s*", "", text, flags=re.IGNORECASE)
    text = text.replace(",", "")
    text = text.strip()

    if not text:
        return None

    try:
        return int(float(text))
    except ValueError:
        return None


def format_date(value: str | None) -> str | None:
    """
    Convert date string to DD/MM/YYYY format.

    Supports formats: DD-Mon-YYYY, DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY
    """
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    formats = [
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue

    return None


def clean_provider_name(value: str | None) -> str | None:
    """Remove "Fullerton Health" from provider name if present."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    cleaned = re.sub(r"\s*-?\s*Fullerton\s+Health\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*Fullerton\s+Health\s*-?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip("-").strip()

    return cleaned if cleaned else None
