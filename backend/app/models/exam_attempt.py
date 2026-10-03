from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)

    # Server-Authoritative Timestamps
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    scheduled_end_time = Column(DateTime(timezone=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Status: IN_PROGRESS, SUBMITTED, TIME_EXPIRED, TERMINATED_VIOLATION
    status = Column(String(30), default="IN_PROGRESS", index=True, nullable=False)
    final_score = Column(Numeric(6, 2), default=0.0)

    # Proctoring & Integrity Telemetry
    reference_photo = Column(Text, nullable=True)  # Base64 data URI of official pre-exam reference photo
    suspicious_score = Column(Integer, default=0, nullable=False)
    integrity_status = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    tab_switch_count = Column(Integer, default=0, nullable=False)
    fullscreen_exit_count = Column(Integer, default=0, nullable=False)
    termination_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    student = relationship("User", back_populates="attempts")
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")
    explanation_responses = relationship("ExplanationResponse", back_populates="attempt", cascade="all, delete-orphan")
    proctoring_events = relationship("ProctoringEvent", back_populates="attempt", cascade="all, delete-orphan", order_by="ProctoringEvent.timestamp")
