"""
SQLite database layer using SQLAlchemy.
Tables: meetings, transcripts
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from app.config import settings

# ─────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────

class Meeting(Base):
    """A meeting record — created when a bot is requested."""

    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Platform identity
    platform = Column(String(32), nullable=False)  # google_meet | teams | zoom
    native_meeting_id = Column(String(255), nullable=False)
    vexa_meeting_id = Column(Integer, nullable=True)  # ID from vexa API
    meeting_url = Column(String(1024), nullable=False)
    # State
    status = Column(
        String(32), nullable=False, default="requested"
    )  # requested | joining | active | completed | failed
    language = Column(String(8), nullable=True)
    bot_name = Column(String(128), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    # AI summary (JSON column)
    summary = Column(Text, nullable=True)  # JSON string
    # Notifications
    telegram_notify = Column(Integer, default=1)  # 1 = yes, 0 = no
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    transcript = relationship(
        "Transcript", back_populates="meeting", uselist=False, cascade="all, delete-orphan"
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        # ORM-level defaults (SQLAlchemy default= is server-side only)
        if self.status is None:
            self.status = "requested"
        if self.telegram_notify is None:
            self.telegram_notify = 1

    __table_args__ = (
        Index("ix_meetings_platform_native", "platform", "native_meeting_id", unique=True),
        Index("ix_meetings_status", "status"),
        Index("ix_meetings_created_at", "created_at"),
    )


class Transcript(Base):
    """Transcript segments and raw JSON for a meeting."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(
        Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # Segments stored as JSON text
    segments = Column(Text, nullable=True)  # JSON string
    # Full API response for debugging / future use
    raw_json = Column(Text, nullable=True)
    # Count of segments (denormalised for quick access)
    segment_count = Column(Integer, default=0)
    fetched_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    meeting = relationship("Meeting", back_populates="transcript")

    def __init__(self, **kw):
        super().__init__(**kw)
        # ORM-level default
        if self.segment_count is None:
            self.segment_count = 0

    __table_args__ = (Index("ix_transcripts_meeting_id", "meeting_id"),)


# ─────────────────────────────────────────────────────────────
# Database lifecycle
# ─────────────────────────────────────────────────────────────

_engine: Engine | None = None
_SessionMaker: sessionmaker | None = None


def get_engine() -> Engine:
    """Lazily create the SQLAlchemy engine from DATABASE_URL."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
            if "sqlite" in settings.DATABASE_URL
            else {},
            echo=False,
        )
    return _engine


def get_session_maker() -> sessionmaker:
    global _SessionMaker
    if _SessionMaker is None:
        _SessionMaker = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionMaker


def get_db():
    """
    Dependency-injection style session context manager for FastAPI.
    Yields a SQLAlchemy session, commits on success, rolls back on exception,
    and always closes the session.

    Usage:
        @app.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    maker = get_session_maker()
    session = maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    Base.metadata.create_all(bind=get_engine())


# ─────────────────────────────────────────────────────────────
# Convenience query helpers
# ─────────────────────────────────────────────────────────────

def create_meeting(
    session: Session,
    platform: str,
    native_meeting_id: str,
    meeting_url: str,
    *,
    vexa_meeting_id: int | None = None,
    language: str | None = None,
    bot_name: str | None = None,
    telegram_notify: int = 1,
) -> Meeting:
    """Create and persist a new meeting record."""
    meeting = Meeting(
        platform=platform,
        native_meeting_id=native_meeting_id,
        meeting_url=meeting_url,
        vexa_meeting_id=vexa_meeting_id,
        language=language,
        bot_name=bot_name,
        telegram_notify=telegram_notify,
        status="requested",
    )
    session.add(meeting)
    session.flush()  # get the ID without committing
    return meeting


def update_meeting_summary(session: Session, meeting_id: int, summary: dict) -> Meeting | None:
    """Store the AI summary JSON in a meeting record."""
    from sqlalchemy import update as sql_update

    stmt = (
        sql_update(Meeting)
        .where(Meeting.id == meeting_id)
        .values(summary=json.dumps(summary))
        .execution_options(synchronize_session="fetch")
    )
    result = session.execute(stmt)
    if result.rowcount == 0:
        return None
    # Fetch the updated row so callers get a fresh object
    return session.get(Meeting, meeting_id)


def store_transcript(
    session: Session,
    meeting_id: int,
    segments: list[dict],
    raw_json: str,
) -> Transcript:
    """Create or replace the transcript for a meeting."""
    # Remove existing if any (shouldn't happen with unique constraint)
    existing = (
        session.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    )
    if existing:
        session.delete(existing)

    transcript = Transcript(
        meeting_id=meeting_id,
        segments=json.dumps(segments),
        raw_json=raw_json,
        segment_count=len(segments),
    )
    session.add(transcript)
    return transcript


def get_meeting_by_platform_id(
    session: Session, platform: str, native_meeting_id: str
) -> Meeting | None:
    """Find a meeting by its platform identity."""
    return (
        session.query(Meeting)
        .filter(Meeting.platform == platform, Meeting.native_meeting_id == native_meeting_id)
        .first()
    )
