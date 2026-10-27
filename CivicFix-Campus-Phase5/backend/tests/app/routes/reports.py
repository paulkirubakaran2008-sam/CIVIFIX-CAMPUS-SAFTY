import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from ..auth import get_current_user
from ..repository import repository, upload_path
from ..schemas import DashboardResponse, DuplicateCandidate, DuplicateCheckRequest, ReportPublic, UserPublic
from ..services.analysis import analysis_service
from ..services.duplicates import find_candidates
from ..services.gemini_analysis import GeminiAnalysisError, analyze_with_gemini
from ..services.image_storage import ImageStorageError, save_image
from ..services.priority_engine import compute_priority

logger = logging.getLogger("civicfix.reports")

router = APIRouter(tags=["reports"])
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def serialise(report: dict) -> ReportPublic:
    return ReportPublic(**report)


async def run_analysis(category: str, description: str, location_name: str, image_bytes: bytes, mime_type: str, support_count: int = 0):
    """Real Gemini vision analysis when configured, with an automatic,
    clearly-labelled fallback to the mock provider on any error, timeout, or
    quota limit -- report submission must never fail just because AI is
    unavailable."""
    try:
        return await analyze_with_gemini(
            image_bytes=image_bytes, mime_type=mime_type, category=category, description=description,
            location_name=location_name, support_count=support_count,
        )
    except GeminiAnalysisError as exc:
        logger.info("Falling back to mock analysis provider: %s", exc)
        return analysis_service.analyze(category, description, location_name, support_count)


@router.post("/reports", response_model=ReportPublic, status_code=status.HTTP_201_CREATED)
async def create_report(
    description: str = Form(..., min_length=10, max_length=1000),
    category: str = Form(...),
    location_name: str = Form(..., min_length=2, max_length=120),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    image: UploadFile = File(...),
    duplicate_of: str | None = Form(None),
    user: UserPublic = Depends(get_current_user),
):
    if category not in {"Garbage overflow", "Pothole", "Water leakage", "Broken streetlight", "Damaged infrastructure", "Other"}:
        raise HTTPException(status_code=422, detail="Choose a valid problem category")
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
    filename = f"{uuid4()}{ALLOWED_TYPES[image.content_type]}"

    try:
        image_url = await save_image(content, filename, image.content_type)
    except ImageStorageError as exc:
        # Persistent storage (e.g. Cloudinary) failed -- fall back to local
        # disk rather than losing the report entirely. This will not survive
        # a redeploy, so it is logged loudly for operators to notice.
        logger.error("Persistent image storage failed, using local disk fallback: %s", exc)
        upload_path(filename).write_bytes(content)
        image_url = f"/uploads/{filename}"

    if duplicate_of:
        original = await repository.get(duplicate_of, user.campus_id, user.id, True)
        if not original:
            raise HTTPException(status_code=404, detail="Selected original incident was not found")

    analysis = await run_analysis(category, description, location_name, content, image.content_type)
    report = await repository.create({
        "user_id": user.id, "campus_id": user.campus_id, "reporter_name": user.name, "image_url": image_url,
        "description": description.strip(), "category": category, "location_name": location_name.strip(),
        "latitude": latitude, "longitude": longitude,
        "ai_provider": analysis.provider, "ai_confidence": analysis.confidence, "severity": analysis.severity,
        "safety_risk": analysis.safety_risk, "people_affected": analysis.people_affected,
        "recommended_action": analysis.recommended_action, "priority_score": analysis.priority_score,
        "priority_level": analysis.priority_level, "priority_breakdown": analysis.priority_breakdown,
        "duplicate_of": duplicate_of,
    })
    return serialise(report)


@router.post("/reports/duplicate-check", response_model=list[DuplicateCandidate])
async def duplicate_check(payload: DuplicateCheckRequest, user: UserPublic = Depends(get_current_user)):
    reports = await repository.for_user(user.campus_id, user.id, True)
    return [DuplicateCandidate(report=serialise(report), similarity=score) for report, score in find_candidates(payload.category, payload.location_name, payload.description, reports)]


@router.post("/reports/{report_id}/support", response_model=ReportPublic)
async def support_report(report_id: str, user: UserPublic = Depends(get_current_user)):
    report = await repository.get(report_id, user.campus_id, user.id, True)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    supporters = list(report.get("supporter_ids", []))
    if user.id not in supporters:
        supporters.append(user.id)
    # Re-run only the priority weighting with the new support count, using
    # the report's existing severity/safety findings -- do not re-run the
    # analysis language heuristics, which would silently overwrite a real
    # Gemini result with the mock provider's guess.
    result = compute_priority(
        category=report["category"], confidence=report["ai_confidence"], severity=report["severity"],
        safety_risk=report["safety_risk"], people_affected=report["people_affected"],
        recommended_action=report["recommended_action"], support_count=len(supporters),
        high_traffic_location=report["people_affected"] >= 90, provider=report["ai_provider"],
    )
    updated = await repository.update(report_id, user.campus_id, {
        "supporter_ids": supporters, "support_count": len(supporters), "priority_score": result.priority_score,
        "priority_level": result.priority_level, "priority_breakdown": result.priority_breakdown,
    })
    return serialise(updated)


@router.post("/reports/{report_id}/analyze", response_model=ReportPublic)
async def analyze_report(report_id: str, user: UserPublic = Depends(get_current_user)):
    report = await repository.get(report_id, user.campus_id, user.id, user.role == "admin")
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    result = analysis_service.analyze(report["category"], report["description"], report["location_name"])
    updated = await repository.apply_analysis(report_id, user.campus_id, {
        "ai_provider": result.provider, "ai_confidence": result.confidence, "severity": result.severity,
        "safety_risk": result.safety_risk, "people_affected": result.people_affected,
        "recommended_action": result.recommended_action, "priority_score": result.priority_score,
        "priority_level": result.priority_level, "priority_breakdown": result.priority_breakdown,
    })
    return serialise(updated)


@router.get("/reports", response_model=list[ReportPublic])
async def list_reports(user: UserPublic = Depends(get_current_user)):
    reports = await repository.for_user(user.campus_id, user.id, user.role == "admin")
    return [serialise(report) for report in reports]


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(user: UserPublic = Depends(get_current_user)):
    reports = await repository.for_user(user.campus_id, user.id, user.role == "admin")
    return DashboardResponse(
        total_reports=len(reports),
        pending_reports=sum(r["status"] != "Resolved" for r in reports),
        resolved_reports=sum(r["status"] == "Resolved" for r in reports),
        recent_reports=[serialise(r) for r in reports[:5]],
    )
