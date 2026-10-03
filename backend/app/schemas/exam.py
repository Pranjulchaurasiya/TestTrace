from datetime import datetime
from pydantic import BaseModel, Field


class QuestionBase(BaseModel):
    question_text: str
    question_type: str  # MCQ, TRUE_FALSE, SHORT_ANSWER, CODING, DEBUGGING
    options_json: str | None = None
    starter_code: str | None = None
    coding_language: str = "python"
    marks: int = 5
    order_num: int = 1


class QuestionCreate(QuestionBase):
    correct_answer: str | None = None
    test_cases_json: str | None = None
    explanation_prompts_json: str | None = None


class QuestionSanitizedResponse(QuestionBase):
    """Sanitized question response sent to students (excludes correct_answer and hidden test cases)."""
    id: int
    exam_id: int
    public_test_cases: list[dict] = []
    explanation_prompts: list[dict] = []

    class Config:
        from_attributes = True


class QuestionDetailResponse(QuestionCreate):
    """Full question response for teachers/examiners."""
    id: int
    exam_id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    title: str
    subject: str
    description: str | None = None
    duration_minutes: int = 30
    total_marks: int = 100
    passing_marks: int = 40
    proctoring_enabled: bool = True
    auto_submit_on_violations: bool = True
    max_violations_threshold: int = 100
    max_tab_switches_threshold: int = 3


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: int
    is_published: bool
    created_by: int | None = None
    created_at: datetime | None = None
    question_count: int = 0

    class Config:
        from_attributes = True
