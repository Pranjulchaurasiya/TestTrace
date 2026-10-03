from datetime import datetime
from pydantic import BaseModel, Field


class ViolationReportRequest(BaseModel):
    attempt_id: int
    violation_type: str  # TAB_SWITCH, FULLSCREEN_EXIT, PASTE_BURST
    metadata: dict | None = None


class ViolationReportResponse(BaseModel):
    attempt_id: int
    violation_type: str
    points_added: int
    total_suspicious_score: int
    tab_switch_count: int
    fullscreen_exit_count: int
    integrity_status: str  # LOW, MEDIUM, HIGH, CRITICAL
    terminate_exam: bool = False
    warning_message: str | None = None


class FrameAnalysisResponse(BaseModel):
    attempt_id: int
    faces_detected: int = 1
    identity_verified: bool = True
    gaze_status: str = "FOCUSED"  # FOCUSED, LOOKING_AWAY
    head_pose_direction: str = "STRAIGHT"  # STRAIGHT, LEFT, RIGHT, UP, DOWN
    phone_detected: bool = False
    violation_detected: str | None = None
    points_added: int = 0
    current_suspicious_score: int = 0
    integrity_status: str = "LOW"
    terminate_exam: bool = False
    warning_message: str | None = None


class ProctorEventDetail(BaseModel):
    id: int
    attempt_id: int
    event_type: str
    severity: str
    points: int
    timestamp: datetime
    metadata_json: str | None = None

    class Config:
        from_attributes = True
