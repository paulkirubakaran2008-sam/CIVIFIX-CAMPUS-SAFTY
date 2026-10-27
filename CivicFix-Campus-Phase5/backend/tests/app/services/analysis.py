"""Explainable Phase 2 analysis contract.

`MockVisionAnalysisService` is deliberately a deterministic development
fallback, not a claimed vision model. It never looks at the uploaded image
-- only the selected category and the report text. It is used automatically
whenever GEMINI_API_KEY is unset, and as the safety-net fallback whenever
the real Gemini provider (see gemini_analysis.py) errors, times out, or hits
a quota limit, so report submission never fails just because AI is down.
"""
from .priority_engine import AnalysisResult, compute_priority

MOCK_PROVIDER = "mock-explainable-v1"


class MockVisionAnalysisService:
    """A transparent fallback based on selected category and report language."""
    profiles = {
        "Garbage overflow": (5.8, 62, "Medium", "Arrange waste collection and clean the affected area."),
        "Pothole": (7.4, 76, "High", "Inspect and repair the road surface; mark the hazard until repaired."),
        "Water leakage": (6.7, 71, "Medium", "Inspect the source, isolate the leak, and repair the pipe or fixture."),
        "Broken streetlight": (6.5, 74, "High", "Inspect the electrical connection and replace the damaged light fitting."),
        "Damaged infrastructure": (7.1, 73, "High", "Inspect the structure, secure the area, and schedule repair."),
        "Other": (4.8, 55, "Low", "Inspect the reported area and determine the appropriate maintenance action."),
    }
    urgent_words = ("danger", "accident", "injury", "urgent", "large", "flood", "exposed", "night", "deep")

    def analyze(self, category: str, description: str, location_name: str, support_count: int = 0) -> AnalysisResult:
        base_severity, confidence, risk, action = self.profiles[category]
        text = description.lower()
        urgency = sum(word in text for word in self.urgent_words)
        severity = min(10.0, round(base_severity + urgency * 0.45, 1))
        confidence = min(96.0, round(confidence + min(len(description) // 80, 8), 1))
        if severity >= 7.0:
            risk = "High"
        elif severity >= 5.5:
            risk = "Medium"
        else:
            risk = "Low"
        people = 90 if any(word in location_name.lower() for word in ("library", "canteen", "main", "hostel")) else 45
        people += urgency * 10
        return compute_priority(
            category=category, confidence=confidence, severity=severity, safety_risk=risk,
            people_affected=people, recommended_action=action, support_count=support_count,
            high_traffic_location=people >= 90, provider=MOCK_PROVIDER,
        )


analysis_service = MockVisionAnalysisService()
