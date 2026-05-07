"""
Tests for app/db.py — SQLite schema and query helpers.
Uses a temporary SQLite database per test.
"""

import json
from datetime import datetime, timezone

import pytest

from app.db import (
    Meeting,
    Transcript,
    create_meeting,
    get_meeting_by_platform_id,
    get_db,
    init_db,
    store_transcript,
    update_meeting_summary,
)


# ─────────────────────────────────────────────────────────────
# Schema tests — model field validation
# ─────────────────────────────────────────────────────────────

class TestMeetingModel:
    def test_default_status(self):
        m = Meeting(
            platform="google_meet",
            native_meeting_id="abc-defg-hij",
            meeting_url="https://meet.google.com/abc-defg-hij",
        )
        assert m.status == "requested"

    def test_telegram_notify_default(self):
        m = Meeting(
            platform="zoom",
            native_meeting_id="999",
            meeting_url="https://zoom.us/j/999",
        )
        assert m.telegram_notify == 1


class TestTranscriptModel:
    def test_segment_count_default(self):
        t = Transcript(meeting_id=1, segments="[]", raw_json="{}")
        assert t.segment_count == 0


# ─────────────────────────────────────────────────────────────
# DB init
# ─────────────────────────────────────────────────────────────

class TestDatabaseInit:
    def test_init_db_creates_tables(self, tmp_path):
        from sqlalchemy import create_engine, inspect

        db_path = tmp_path / "test_init.db"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{db_path}")
        from app.db import Base
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "meetings" in tables
        assert "transcripts" in tables


# ─────────────────────────────────────────────────────────────
# CRUD helpers
# ─────────────────────────────────────────────────────────────

class TestCreateMeeting:
    def test_create_meeting(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{tmp_path}/crud.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as session:
            m = create_meeting(
                session,
                platform="google_meet",
                native_meeting_id="abc-defg-hij",
                meeting_url="https://meet.google.com/abc-defg-hij",
                language="es",
                bot_name="Meety",
                telegram_notify=1,
            )
            session.commit()

        assert m.id is not None
        assert m.platform == "google_meet"
        assert m.status == "requested"
        assert m.telegram_notify == 1
        assert m.created_at is not None

    def test_create_meeting_unique_constraint(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.exc import IntegrityError

        engine = create_engine(f"sqlite:///{tmp_path}/unique.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as s1:
            create_meeting(
                s1, platform="google_meet", native_meeting_id="dup",
                meeting_url="https://meet.google.com/dup",
            )
            s1.commit()

            with pytest.raises(IntegrityError):
                create_meeting(
                    s1, platform="google_meet", native_meeting_id="dup",
                    meeting_url="https://meet.google.com/dup2",
                )
                s1.commit()


class TestGetMeetingByPlatformId:
    def test_finds_existing(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{tmp_path}/find.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as s:
            created = create_meeting(
                s, platform="teams", native_meeting_id="123456",
                meeting_url="https://teams.live.com/meet/123456",
            )
            s.commit()

        with maker() as s:
            found = get_meeting_by_platform_id(s, "teams", "123456")
            assert found is not None
            assert found.id == created.id

    def test_returns_none_for_missing(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{tmp_path}/notfound.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as s:
            found = get_meeting_by_platform_id(s, "zoom", "nonexistent")
            assert found is None


class TestStoreTranscript:
    def test_stores_segments(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{tmp_path}/trans.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as s:
            meeting = create_meeting(
                s, platform="google_meet", native_meeting_id="seg-test",
                meeting_url="https://meet.google.com/seg-test",
            )
            s.commit()
            meeting_id = meeting.id

        segments = [
            {"start_time": 0.0, "end_time": 3.0, "text": "Hello.", "speaker": "Alice"},
            {"start_time": 3.0, "end_time": 7.0, "text": "How are you?", "speaker": "Bob"},
        ]
        raw = json.dumps({"id": 1, "platform": "google_meet", "segments": segments})

        with maker() as s:
            t = store_transcript(s, meeting_id, segments, raw)
            s.commit()

        assert t.meeting_id == meeting_id
        assert t.segment_count == 2
        parsed = json.loads(t.segments)
        assert len(parsed) == 2
        assert parsed[0]["speaker"] == "Alice"


class TestUpdateMeetingSummary:
    def test_stores_json_summary(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{tmp_path}/summary.db")
        from app.db import Base
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        with maker() as s:
            meeting = create_meeting(
                s, platform="google_meet", native_meeting_id="sum-test",
                meeting_url="https://meet.google.com/sum-test",
            )
            s.commit()
            meeting_id = meeting.id

        summary = {
            "executive_summary": "Q1 planning completed.",
            "tasks": [{"description": "Send report", "assignee": "Alice", "due": "2026-05-10"}],
            "commitments": [],
            "key_points": ["Budget approved", "Hiring freeze lifted"],
            "next_meeting": None,
        }

        with maker() as s:
            update_meeting_summary(s, meeting_id, summary)
            s.commit()

        with maker() as s:
            from app.db import Meeting
            m = s.get(Meeting, meeting_id)
            assert m.summary is not None
            parsed = json.loads(m.summary)
            assert parsed["executive_summary"] == "Q1 planning completed."
            assert len(parsed["tasks"]) == 1
