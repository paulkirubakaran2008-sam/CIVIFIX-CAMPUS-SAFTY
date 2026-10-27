"""Real Gemini vision analysis provider.

GEMINI_API_KEY is read only from backend environment variables (see
config.py) and never sent to, or accepted from, the frontend. Call
`analyze_with_gemini(...)`; on any failure it raises `GeminiAnalysisError`
and the caller (routes/reports.py) falls back to the mock provider so a
report submission never fails just because Gemini is down or unconfigured.
"""
import base64
import json
import logging

import httpx

from ..config import get_settings
from .priority_engine import AnalysisResult, compute_priority

logger = logging.getLogger("civicfix.gemini")

GEMINI_PROVIDER = "gemini-vision-v1"

CATEGORIES = ["Garbage overflow", "Pothole", "Water leakage", "Broken streetlight", "Damaged infrastructure", "Other"]

PROMPT_TEMPLATE = """You are an assistant that triages campus facilities-maintenance reports for CivicFix.

A student uploaded a photo and filled in this report:
- Selected category: {category}
- Location: {location_name}
- Description: {description}

Look at the photo and respond with ONLY a JSON object (no markdown fences, no extra text) with exactly these fields:
{{
  "image_matches_category": true or false (does the photo plausibly show a "{category}" problem?),
  "confidence": number 0-100 (how confident you are in your assessment of the photo),
  "severity": number 0-10 (how severe the problem looks),
  "safety_risk": "Low" or "Medium" or "High",
  "people_affected_estimate": integer (rough estimate of people affected per day based on the location and problem),
  "recommended_action": short string, one practical next step for campus facilities staff
}}
"""


class GeminiAnalysisError(Exception):
    pass


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise GeminiAnalysisError("Gemini response did not contain a JSON object")
    return json.loads(cleaned[start : end + 1])


async def analyze_with_gemini(
    *, image_bytes: bytes, mime_type: str, category: str, description: str, location_name: str, support_count: int,
) -> AnalysisResult:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiAnalysisError("GEMINI_API_KEY is not configured")
    if category not in CATEGORIES:
        raise GeminiAnalysisError("Unsupported category")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    prompt = PROMPT_TEMPLATE.format(category=category, location_name=location_name, description=description)
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
            response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
    except httpx.TimeoutException as exc:
        raise GeminiAnalysisError("Gemini request timed out") from exc
    except httpx.HTTPError as exc:
        raise GeminiAnalysisError("Gemini request failed") from exc

    if response.status_code == 429:
        raise GeminiAnalysisError("Gemini quota exceeded")
    if response.status_code != 200:
        # Never surface response.text here: it can echo the request, including
        # the key, back in some error payloads.
        logger.warning("Gemini API returned status %s", response.status_code)
        raise GeminiAnalysisError(f"Gemini API error {response.status_code}")

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _extract_json(text)
    except (KeyError, IndexError, json.JSONDecodeError, GeminiAnalysisError) as exc:
        raise GeminiAnalysisError("Could not parse Gemini response") from exc

    try:
        severity = max(0.0, min(10.0, float(parsed["severity"])))
        confidence = max(0.0, min(100.0, float(parsed["confidence"])))
        safety_risk = parsed["safety_risk"] if parsed["safety_risk"] in {"Low", "Medium", "High"} else "Medium"
        people_affected = max(0, int(parsed["people_affected_estimate"]))
        recommended_action = str(parsed["recommended_action"])[:300]
    except (KeyError, TypeError, ValueError) as exc:
        raise GeminiAnalysisError("Gemini response was missing required fields") from exc

    if parsed.get("image_matches_category") is False:
        confidence = min(confidence, 40.0)

    return compute_priority(
        category=category, confidence=confidence, severity=severity, safety_risk=safety_risk,
        people_affected=people_affected, recommended_action=recommended_action, support_count=support_count,
        high_traffic_location=people_affected >= 90, provider=GEMINI_PROVIDER,
    )
