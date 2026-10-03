from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event types: TAB_SWITCH, FULLSCREEN_EXIT, PASTE_BURST, FACE_MISSING,
    # LOOKING_LEFT, LOOKING_RIGHT, LOOKING_UP, LOOKING_DOWN, LOOKING_AWAY,
    # MULTIPLE_FACES, PHONE_DETECTED
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    points = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json = Column(Text, nullable=True)  # Store detailed telemetry (angles, paste length, etc.)

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="proctoring_events")
