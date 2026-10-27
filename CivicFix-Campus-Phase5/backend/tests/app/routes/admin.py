from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException
from ..auth import require_admin
from ..repository import repository
from ..schemas import AdminDashboardResponse, AssignmentRequest, ReportPublic, StatusRequest, UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


def serialise(report: dict) -> ReportPublic:
    return ReportPublic(**report)


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def dashboard(admin: UserPublic = Depends(require_admin)):
    reports = await repository.for_user(admin.campus_id, admin.id, True)
    queue = sorted(reports, key=lambda report: report.get("priority_score", 0), reverse=True)
    return AdminDashboardResponse(
        total_reports=len(reports), pending_reports=sum(report["status"] in {"Reported", "AI Verified", "Assigned"} for report in reports),
        in_progress_reports=sum(report["status"] == "In Progress" for report in reports),
        resolved_reports=sum(report["status"] == "Resolved" for report in reports),
        high_priority_reports=sum(report.get("priority_level") in {"High", "Critical"} for report in reports),
        priority_queue=[serialise(report) for report in queue],
    )


@router.put("/reports/{report_id}/assignment", response_model=ReportPublic)
async def assign_report(report_id: str, payload: AssignmentRequest, admin: UserPublic = Depends(require_admin)):
    report = await repository.get(report_id, admin.campus_id, admin.id, True)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    updated = await repository.update(report_id, admin.campus_id, {"assigned_to": payload.assigned_to, "status": "Assigned"})
    return serialise(updated)


@router.put("/reports/{report_id}/status", response_model=ReportPublic)
async def change_status(report_id: str, payload: StatusRequest, admin: UserPublic = Depends(require_admin)):
    report = await repository.get(report_id, admin.campus_id, admin.id, True)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    changes = {"status": payload.status}
    if payload.resolution_note:
        changes["resolution_note"] = payload.resolution_note
    if payload.status == "Resolved":
        changes["resolved_at"] = datetime.now(UTC)
    updated = await repository.update(report_id, admin.campus_id, changes)
    return serialise(updated)
