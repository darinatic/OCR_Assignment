"""Claude Vision API integration for document extraction."""

import base64
import json
import re
import os
from typing import Any

import anthropic

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def build_extraction_prompt() -> str:
    """Build the extraction prompt for Claude."""
    return """Classify this medical document and extract relevant fields.

## Document Types
- "referral_letter": A letter referring a patient to another healthcare provider or specialist
- "medical_certificate": A certificate for medical leave (MC/sick leave), stating the patient is unfit for work
- "receipt": A payment receipt or invoice for medical services
- "other": Documents that don't fit the above 

## Extraction Fields (Description → JSON key)

For referral_letter:
- Patient Name → claimant_name
- Provider/Lab name (exclude "Fullerton Health") → provider_name
- Handwritten signature detected → signature_presence (boolean)
- Total amount paid → total_amount_paid (integer)
- Approved amount → total_approved_amount (integer)
- Requested amount → total_requested_amount (integer)

For medical_certificate:
- Claimant Name → claimant_name
- Address → claimant_address
- Date of Birth → claimant_date_of_birth
- Diagnosis → diagnosis_name
- Discharge date → discharge_date_time
- ICD code → icd_code
- Provider/Lab name (exclude "Fullerton Health") → provider_name
- Admission datetime → submission_date_time
- Date of MC → date_of_mc
- Number of MC days → mc_days (integer)

For receipt:
- Claimant Name → claimant_name
- Address → claimant_address
- Date of Birth → claimant_date_of_birth
- Provider/Lab name (exclude "Fullerton Health") → provider_name
- Tax amount → tax_amount (integer)
- Total amount → total_amount (integer)

## Output
Return JSON only:
{"document_type": "<type>", "fields": {...}}

Use null for fields not found. For "other", return empty fields: {"document_type": "other", "fields": {}}"""


def parse_claude_response(response_text: str) -> dict[str, Any]:
    """Parse JSON from Claude's response, handling markdown code blocks."""
    text = response_text.strip()

    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from response: {e}")


async def extract_document_data(images: list[bytes]) -> dict[str, Any]:
    """Extract document data using Claude Vision API."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    content: list[dict[str, Any]] = []

    for img_bytes in images:
        b64_image = base64.b64encode(img_bytes).decode("utf-8")
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64_image,
            },
        })

    content.append({
        "type": "text",
        "text": build_extraction_prompt(),
    })

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )

    response_text = message.content[0].text
    return parse_claude_response(response_text)
