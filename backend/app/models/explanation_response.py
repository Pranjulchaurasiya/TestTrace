from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class ExplanationResponse(Base):
    __tablename__ = "explanation_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    prompt_index = Column(Integer, default=0, nullable=False)
    prompt_text = Column(Text, nullable=False)
    student_explanation = Column(Text, nullable=False)
    response_time_seconds = Column(Numeric(5, 2), nullable=True)
    is_timed_out = Column(Boolean, default=False, nullable=False)

    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="explanation_responses")
    question = relationship("Question", back_populates="explanation_responses")
