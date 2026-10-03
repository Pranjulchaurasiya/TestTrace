from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), nullable=False)  # MCQ, TRUE_FALSE, SHORT_ANSWER, CODING, DEBUGGING

    # Structure payloads stored as JSON strings
    options_json = Column(Text, nullable=True)  # [{"id": "A", "text": "Option 1"}]
    correct_answer = Column(Text, nullable=True)  # For automated scoring (MCQ/TF or reference)
    starter_code = Column(Text, nullable=True)  # Boilerplate for coding/debugging
    coding_language = Column(String(30), default="python")  # python, java, cpp, c
    test_cases_json = Column(Text, nullable=True)  # [{"input": "...", "expected_output": "...", "is_hidden": false}]
    explanation_prompts_json = Column(Text, nullable=True)  # Mini-viva prompts: [{"prompt": "...", "timer_seconds": 45}]

    marks = Column(Integer, default=5, nullable=False)
    order_num = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")
    explanation_responses = relationship("ExplanationResponse", back_populates="question", cascade="all, delete-orphan")
