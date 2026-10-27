from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


Category = Literal["Garbage overflow", "Pothole", "Water leakage", "Broken streetlight", "Damaged infrastructure", "Other"]
Status = Literal["Reported", "AI Verified", "Assigned", "In Progress", "Resolved", "Reopened"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal["student", "admin"]
    campus_id: str
    campus_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ReportPublic(BaseModel):
    id: str
    report_id: str
    user_id: str
    campus_id: str
    reporter_name: str
    image_url: str | None = None
    description: str
    category: Category
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    status: Status
    ai_provider: str | None = None
    ai_confidence: float | None = None
    severity: float | None = None
    safety_risk: Literal["Low", "Medium", "High"] | None = None
    people_affected: int | None = None
    recommended_action: str | None = None
    priority_score: float | None = None
    priority_level: Literal["Low", "Medium", "High", "Critical"] | None = None
    priority_breakdown: dict[str, float] | None = None
    duplicate_of: str | None = None
    duplicate_similarity: float | None = None
    support_count: int = 0
    assigned_to: str | None = None
    resolution_note: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class DashboardResponse(BaseModel):
    total_reports: int
    pending_reports: int
    resolved_reports: int
    recent_reports: list[ReportPublic]


class DuplicateCheckRequest(BaseModel):
    category: Category
    location_name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=1000)


class DuplicateCandidate(BaseModel):
    report: ReportPublic
    similarity: float


class AssignmentRequest(BaseModel):
    assigned_to: str = Field(min_length=2, max_length=120)


class StatusRequest(BaseModel):
    status: Status
    resolution_note: str | None = Field(default=None, max_length=1000)


class AdminDashboardResponse(BaseModel):
    total_reports: int
    pending_reports: int
    in_progress_reports: int
    resolved_reports: int
    high_priority_reports: int
    priority_queue: list[ReportPublic]
