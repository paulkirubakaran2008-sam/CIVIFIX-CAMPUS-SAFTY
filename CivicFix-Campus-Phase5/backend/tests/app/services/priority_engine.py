"""Single source of truth for the explainable priority score.

Both the mock analysis provider and the real Gemini provider funnel their
raw findings (severity, safety risk, people affected, support count) through
this module, so the documented weighting (severity 30%, safety risk 25%,
people affected 20%, supporting reports 15%, location importance 10%) is
only defined once.
"""
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    detected_category: str
    confidence: float
    severity: float
    safety_risk: str
    people_affected: int
    recommended_action: str
    priority_score: float
    priority_level: str
    priority_breakdown: dict[str, float]
    provider: str


def priority_level_for(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def compute_priority(
    *,
    category: str,
    confidence: float,
    severity: float,
    safety_risk: str,
    people_affected: int,
    recommended_action: str,
    support_count: int,
    high_traffic_location: bool,
    provider: str,
) -> AnalysisResult:
    safety = {"Low": 30, "Medium": 60, "High": 90}.get(safety_risk, 60)
    people_factor = min(100, people_affected)
    support_factor = min(100, support_count * 20)
    location_factor = 80 if high_traffic_location else 50
    breakdown = {
        "severity": round(severity * 10 * 0.30, 1),
        "safety_risk": round(safety * 0.25, 1),
        "people_affected": round(people_factor * 0.20, 1),
        "supporting_reports": round(support_factor * 0.15, 1),
        "location_importance": round(location_factor * 0.10, 1),
    }
    score = round(sum(breakdown.values()), 1)
    return AnalysisResult(
        detected_category=category,
        confidence=confidence,
        severity=severity,
        safety_risk=safety_risk,
        people_affected=people_affected,
        recommended_action=recommended_action,
        priority_score=score,
        priority_level=priority_level_for(score),
        priority_breakdown=breakdown,
        provider=provider,
    )
