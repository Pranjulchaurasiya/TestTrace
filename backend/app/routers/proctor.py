import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.exam import Exam
from app.models.exam_attempt import ExamAttempt
from app.models.proctoring_event import ProctoringEvent
from app.models.user import User
from app.schemas.proctor import (
    FrameAnalysisResponse,
    ProctorEventDetail,
    ViolationReportRequest,
    ViolationReportResponse,
)
from app.ai.proctor_service import analyze_frame_telemetry, calculate_risk_level
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/proctor", tags=["AI Proctoring & Telemetry"])


@router.post("/violation", response_model=ViolationReportResponse)
def report_violation(
    payload: ViolationReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logs browser-level telemetry events: TAB_SWITCH, FULLSCREEN_EXIT, PASTE_BURST."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == payload.attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()

    points_added = 0
    v_type = payload.violation_type.upper()
    warning_msg = None
    terminate_exam = False

    if v_type == "TAB_SWITCH":
        points_added = 5
        attempt.tab_switch_count += 1
        current_switches = attempt.tab_switch_count
        max_allowed = exam.max_tab_switches_threshold if exam else 3

        if current_switches >= max_allowed:
            terminate_exam = True
            attempt.status = "TERMINATED_VIOLATION"
            attempt.termination_reason = f"Exceeded maximum tab switches limit ({max_allowed})"
            warning_msg = f"Final violation: Tab switch limit ({max_allowed}) reached. Examination has been automatically terminated."
        else:
            warning_msg = f"Warning {current_switches} of {max_allowed}: Tab switching is strictly prohibited."

    elif v_type == "FULLSCREEN_EXIT":
        points_added = 5
        attempt.fullscreen_exit_count += 1
        warning_msg = "Warning: Fullscreen mode was exited. Please re-enter fullscreen immediately."

    elif v_type == "PASTE_BURST":
        points_added = 3
        warning_msg = "Notice: Large clipboard paste burst detected."

    else:
        points_added = 2
        warning_msg = f"Notice: Unregistered violation recorded ({payload.violation_type})."

    attempt.suspicious_score += points_added
    attempt.integrity_status = calculate_risk_level(attempt.suspicious_score)

    if attempt.suspicious_score >= 100 and not terminate_exam:
        terminate_exam = True
        attempt.status = "TERMINATED_VIOLATION"
        attempt.termination_reason = "Suspicious activity score exceeded critical threshold (100)"
        warning_msg = "Critical violation: Cumulative suspicious score reached 100. Examination terminated."

    # Persist proctoring event
    now_utc = datetime.now(timezone.utc)
    event = ProctoringEvent(
        attempt_id=attempt.id,
        event_type=v_type,
        severity="CRITICAL" if terminate_exam else "WARNING",
        points=points_added,
        timestamp=now_utc,
        metadata_json=json.dumps(payload.metadata or {}),
    )
    db.add(event)
    db.commit()

    return ViolationReportResponse(
        attempt_id=attempt.id,
        violation_type=v_type,
        points_added=points_added,
        total_suspicious_score=attempt.suspicious_score,
        tab_switch_count=attempt.tab_switch_count,
        fullscreen_exit_count=attempt.fullscreen_exit_count,
        integrity_status=attempt.integrity_status,
        terminate_exam=terminate_exam,
        warning_message=warning_msg,
    )


@router.post("/analyze-frame", response_model=FrameAnalysisResponse)
async def analyze_camera_frame(
    attempt_id: int = Form(...),
    frame: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Processes compressed camera frame for face presence, multiple faces, and head pose."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt or attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden or attempt not found")

    image_bytes = await frame.read()
    analysis = analyze_frame_telemetry(image_bytes, attempt_id=attempt.id)

    violation = analysis.get("violation")
    points = analysis.get("points", 0)
    terminate_exam = False
    warning_msg = None

    if violation == "FACE_MISMATCH":
        warning_msg = "Identity Alert: Candidate face does not match the enrolled student."
    elif violation == "PHONE_DETECTED":
        warning_msg = "Critical Alert: Unauthorized mobile device detected in frame."

    if violation and attempt.status == "IN_PROGRESS":
        attempt.suspicious_score += points
        attempt.integrity_status = calculate_risk_level(attempt.suspicious_score)

        if attempt.suspicious_score >= 100:
            terminate_exam = True
            attempt.status = "TERMINATED_VIOLATION"
            attempt.termination_reason = "Critical suspicious activity score limit reached (100)"
            warning_msg = "Critical violation: Cumulative suspicious score reached 100. Examination terminated."

        event = ProctoringEvent(
            attempt_id=attempt.id,
            event_type=violation,
            severity="CRITICAL" if terminate_exam else "WARNING",
            points=points,
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps(analysis.get("metadata", {})),
        )
        db.add(event)
        db.commit()

    return FrameAnalysisResponse(
        attempt_id=attempt.id,
        faces_detected=analysis.get("faces_detected", 1),
        identity_verified=analysis.get("identity_verified", True),
        gaze_status=analysis.get("gaze_status", "FOCUSED"),
        head_pose_direction=analysis.get("head_pose_direction", "STRAIGHT"),
        phone_detected=analysis.get("phone_detected", False),
        violation_detected=violation,
        points_added=points,
        current_suspicious_score=attempt.suspicious_score,
        integrity_status=attempt.integrity_status,
        terminate_exam=terminate_exam,
        warning_message=warning_msg,
    )


@router.get("/attempts/{attempt_id}/events", response_model=list[ProctorEventDetail])
def get_attempt_events(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full chronological proctoring timeline for review."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    events = (
        db.query(ProctoringEvent)
        .filter(ProctoringEvent.attempt_id == attempt_id)
        .order_by(ProctoringEvent.timestamp.asc())
        .all()
    )
    return events
