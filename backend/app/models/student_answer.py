from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, Boolean, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.database import Base


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    submitted_answer = Column(Text, nullable=True)
    execution_output = Column(Text, nullable=True)  # Sandbox test runner output
    is_correct = Column(Boolean, nullable=True)
    marks_awarded = Column(Numeric(5, 2), default=0.0)
    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
