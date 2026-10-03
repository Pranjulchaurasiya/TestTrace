from datetime import datetime
from pydantic import BaseModel, Field


class ProctoringConfig(BaseModel):
    proctoring_enabled: bool = True
    auto_submit_on_violations: bool = True
    max_violations_threshold: int = 100
    max_tab_switches_threshold: int = 3


class AttemptStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    title: str
    subject: str
    duration_minutes: int
    total_marks: int
    start_time_utc: datetime
    scheduled_end_time_utc: datetime
    server_time_utc: datetime
    remaining_seconds: int
    proctoring_config: ProctoringConfig


class TimeSyncResponse(BaseModel):
    attempt_id: int
    server_time_utc: datetime
    scheduled_end_time_utc: datetime
    remaining_seconds: int
    is_expired: bool


class AnswerSubmitRequest(BaseModel):
    question_id: int
    submitted_answer: str
    execution_output: str | None = None


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    is_correct: bool | None = None
    marks_awarded: float = 0.0
    answered_at: datetime | None = None


class VivaSubmitRequest(BaseModel):
    question_id: int
    prompt_index: int = 0
    prompt_text: str
    student_explanation: str
    response_time_seconds: float | None = None


class VivaResponse(BaseModel):
    id: int
    question_id: int
    prompt_index: int
    student_explanation: str
    submitted_at: datetime | None = None


class AttemptResultResponse(BaseModel):
    attempt_id: int
    student_id: int
    student_name: str
    exam_id: int
    exam_title: str
    status: str  # SUBMITTED, TIME_EXPIRED, TERMINATED_VIOLATION
    final_score: float
    total_marks: int
    passing_marks: int
    passed: bool
    start_time: datetime
    submitted_at: datetime | None = None
    suspicious_score: int
    integrity_status: str  # LOW, MEDIUM, HIGH, CRITICAL
    tab_switch_count: int
    fullscreen_exit_count: int
    termination_reason: str | None = None
    total_questions: int
    answered_count: int
