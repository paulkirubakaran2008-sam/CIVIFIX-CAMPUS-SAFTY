"""Phase 5 explainable recurring-issue predictor.

This intentionally uses count/trend rules instead of claiming a trained ML model.
When the local database has too little history, it returns explicitly fictional
demo signals so the college project can still be demonstrated honestly.
"""
from collections import Counter


DEMO_SIGNALS = [
    {"category": "Garbage overflow", "location_name": "Canteen", "probability": 82, "evidence": "Fictional demo dataset: reports increased for 3 consecutive weeks.", "recommendation": "Increase waste collection frequency between 12 PM and 2 PM."},
    {"category": "Water leakage", "location_name": "Hostel Block B", "probability": 68, "evidence": "Fictional demo dataset: repeated reports in the same maintenance zone.", "recommendation": "Schedule a preventative plumbing inspection this week."},
]


def predict(reports: list[dict]) -> dict:
    active = [report for report in reports if report["status"] != "Resolved"]
    if len(reports) < 6:
        return {"is_demo_data": True, "method": "rule-based recurring-pattern demo", "minimum_history": 6, "predictions": DEMO_SIGNALS}
    counts = Counter((report["category"], report["location_name"]) for report in active)
    predictions = []
    for (category, location), count in counts.most_common():
        if count < 2:
            continue
        probability = min(92, 45 + count * 14)
        predictions.append({
            "category": category, "location_name": location, "probability": probability,
            "evidence": f"{count} unresolved reports share this category and campus location.",
            "recommendation": f"Plan preventative inspection and maintenance at {location} before the issue recurs.",
        })
    return {"is_demo_data": False, "method": "explainable frequency-based recurring-pattern model", "minimum_history": 6, "predictions": predictions[:5]}
