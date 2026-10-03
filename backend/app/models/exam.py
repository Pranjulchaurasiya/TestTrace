from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    total_marks = Column(Integer, default=100, nullable=False)
    passing_marks = Column(Integer, default=40, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    proctoring_enabled = Column(Boolean, default=True, nullable=False)
    auto_submit_on_violations = Column(Boolean, default=True, nullable=False)
    max_violations_threshold = Column(Integer, default=100, nullable=False)
    max_tab_switches_threshold = Column(Integer, default=3, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User", back_populates="created_exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan", order_by="Question.order_num")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")
