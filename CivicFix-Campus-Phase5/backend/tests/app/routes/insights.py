from collections import Counter, defaultdict
from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ..repository import repository
from ..schemas import ReportPublic, UserPublic
from ..services.predictions import predict

router = APIRouter(tags=["insights"])


def serialise(report: dict) -> ReportPublic:
    return ReportPublic(**report)


@router.get("/map/reports", response_model=list[ReportPublic])
async def map_reports(user: UserPublic = Depends(get_current_user)):
    """Authenticated map feed; reports without coordinates receive campus demo coordinates."""
    reports = await repository.for_user(user.campus_id, user.id, True)
    enriched = []
    for index, report in enumerate(reports):
        item = report.copy()
        item["latitude"] = item["latitude"] if item.get("latitude") is not None else 12.9716 + (index % 4) * 0.0014
        item["longitude"] = item["longitude"] if item.get("longitude") is not None else 77.5946 + (index % 5) * 0.0012
        enriched.append(item)
    return [serialise(report) for report in enriched]


@router.get("/analytics")
async def analytics(user: UserPublic = Depends(get_current_user)):
    reports = await repository.for_user(user.campus_id, user.id, True)
    by_category = Counter(report["category"] for report in reports)
    by_location = Counter(report["location_name"] for report in reports)
    by_status = Counter(report["status"] for report in reports)
    daily = defaultdict(int)
    for report in reports:
        daily[report["created_at"].date().isoformat()] += 1
    resolved = [report for report in reports if report["status"] == "Resolved" and report.get("resolved_at")]
    average_resolution_hours = round(sum((report["resolved_at"] - report["created_at"]).total_seconds() / 3600 for report in resolved) / len(resolved), 1) if resolved else None
    return {
        "is_demo_data": not bool(reports),
        "reports_by_category": [{"name": key, "value": value} for key, value in by_category.most_common()],
        "reports_by_location": [{"name": key, "value": value} for key, value in by_location.most_common()],
        "reports_by_status": [{"name": key, "value": value} for key, value in by_status.most_common()],
        "reports_over_time": [{"date": key, "count": value} for key, value in sorted(daily.items())],
        "average_resolution_hours": average_resolution_hours,
        "most_problematic_area": by_location.most_common(1)[0][0] if by_location else None,
    }


@router.get("/predictions")
async def predictions(user: UserPublic = Depends(get_current_user)):
    reports = await repository.for_user(user.campus_id, user.id, True)
    return predict(reports)
