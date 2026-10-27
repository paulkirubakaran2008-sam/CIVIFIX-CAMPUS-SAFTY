"""Transparent duplicate detection based on Phase 3 text/location features."""
import re


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def similarity(category: str, location: str, description: str, report: dict) -> float:
    if category != report["category"]:
        return 0.0
    description_tokens = _tokens(description)
    existing_tokens = _tokens(report["description"])
    text_score = len(description_tokens & existing_tokens) / max(1, len(description_tokens | existing_tokens))
    location_score = 1.0 if location.strip().lower() == report["location_name"].strip().lower() else 0.0
    return round((0.45 + 0.35 * location_score + 0.20 * text_score) * 100, 1)


def find_candidates(category: str, location: str, description: str, reports: list[dict]) -> list[tuple[dict, float]]:
    matches = [(report, similarity(category, location, description, report)) for report in reports if report["status"] != "Resolved"]
    return sorted(((report, score) for report, score in matches if score >= 55), key=lambda item: item[1], reverse=True)
