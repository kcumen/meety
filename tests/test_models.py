"""
Tests for app/models.py — Pydantic schemas.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import (
    CommitmentItem,
    JoinMeetingRequest,
    JoinMeetingResponse,
    MeetingListResponse,
    MeetingResponse,
    MeetingStatus,
    MeetingSummary,
    MeetingSummaryResponse,
    MeetingStatusResponse,
    Platform,
    TaskItem,
    TranscriptResponse,
    TranscriptSegmentResponse,
    VexaRecordingCompletedEvent,
    VexaStatusChangeEvent,
    WebhookResponse,
)


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class TestEnums:
    def test_platform_values(self):
        assert Platform.google_meet.value == "google_meet"
        assert Platform.teams.value == "teams"
        assert Platform.zoom.value == "zoom"

    def test_meeting_status_values(self):
        assert MeetingStatus.requested.value == "requested"
        assert MeetingStatus.completed.value == "completed"
        assert MeetingStatus.failed.value == "failed"


# ─────────────────────────────────────────────────────────────
# JoinMeetingRequest
# ─────────────────────────────────────────────────────────────

class TestJoinMeetingRequest:
    def test_valid_google_meet_url(self):
        req = JoinMeetingRequest(url="https://meet.google.com/abc-defg-hij")
        assert str(req.url) == "https://meet.google.com/abc-defg-hij"

    def test_defaults(self):
        req = JoinMeetingRequest(url="https://teams.live.com/meet/123456")
        assert req.language is None
        assert req.bot_name == "Meety"
        assert req.transcribe_enabled is True
        assert req.recording_enabled is False
        assert req.notify_telegram is True

    def test_all_fields(self):
        req = JoinMeetingRequest(
            url="https://zoom.us/j/123456",
            language="es",
            bot_name="MyBot",
            transcribe_enabled=True,
            recording_enabled=True,
            transcription_tier="deferred",
            notify_telegram=False,
        )
        assert req.language == "es"
        assert req.bot_name == "MyBot"
        assert req.transcription_tier == "deferred"
        assert req.notify_telegram is False

    def test_invalid_url_rejected(self):
        with pytest.raises(ValidationError):
            JoinMeetingRequest(url="not-a-url")

    def test_strips_whitespace(self):
        req = JoinMeetingRequest(url="  https://meet.google.com/abc  ")
        assert "abc" in str(req.url)


# ─────────────────────────────────────────────────────────────
# Response models
# ─────────────────────────────────────────────────────────────

class TestMeetingResponse:
    def test_from_attributes(self):
        from app.db import Meeting

        m = Meeting(
            platform="google_meet",
            native_meeting_id="abc",
            meeting_url="https://meet.google.com/abc",
            status="active",
            telegram_notify=1,
        )
        m.id = 5
        m.created_at = datetime.now(timezone.utc)
        m.updated_at = datetime.now(timezone.utc)

        r = MeetingResponse.model_validate(m)
        assert r.id == 5
        assert r.platform == "google_meet"
        assert r.telegram_notify is True


class TestJoinMeetingResponse:
    def test_fields(self):
        r = JoinMeetingResponse(
            id=1,
            platform="google_meet",
            native_meeting_id="abc",
            vexa_bot_id=219,
            status="requested",
            meeting_url="https://meet.google.com/abc",
        )
        assert r.id == 1
        assert r.vexa_bot_id == 219


class TestMeetingStatusResponse:
    def test_defaults(self):
        r = MeetingStatusResponse(status="requested")
        assert r.segments_so_far == 0
        assert r.vexa_bot_id is None


# ─────────────────────────────────────────────────────────────
# Summary models
# ─────────────────────────────────────────────────────────────

class TestTaskItem:
    def test_full(self):
        t = TaskItem(description="Send report", assignee="Alice", due="2026-05-10", priority="high")
        assert t.assignee == "Alice"
        assert t.priority == "high"

    def test_minimal(self):
        t = TaskItem(description="Follow up")
        assert t.assignee is None
        assert t.due is None
        assert t.priority is None


class TestCommitmentItem:
    def test_full(self):
        c = CommitmentItem(description="Call client tomorrow", by="Bob", due="2026-05-08")
        assert c.by == "Bob"

    def test_minimal(self):
        c = CommitmentItem(description="Send invoice")
        assert c.by is None


class TestMeetingSummary:
    def test_full(self):
        s = MeetingSummary(
            executive_summary="Discussed Q2 roadmap.",
            tasks=[TaskItem(description="Prepare deck", assignee="Alice")],
            commitments=[CommitmentItem(description="Call client", by="Bob")],
            key_points=["Budget approved", "Hiring freeze lifted"],
            next_meeting="Next Tuesday",
            generated_at=datetime.now(timezone.utc),
            model="claude-sonnet-4",
        )
        assert len(s.tasks) == 1
        assert len(s.commitments) == 1
        assert len(s.key_points) == 2


class TestMeetingSummaryResponse:
    def test_has_both_summary_and_text(self):
        r = MeetingSummaryResponse(
            meeting_id=1,
            platform="google_meet",
            native_meeting_id="abc",
            summary=MeetingSummary(
                executive_summary="Done.",
                tasks=[],
                commitments=[],
                generated_at=datetime.now(timezone.utc),
            ),
            summary_text=None,
        )
        assert r.summary is not None
        assert r.summary.executive_summary == "Done."


# ─────────────────────────────────────────────────────────────
# Transcript
# ─────────────────────────────────────────────────────────────

class TestTranscriptSegmentResponse:
    def test_fields(self):
        s = TranscriptSegmentResponse(
            start_time=0.0,
            end_time=3.0,
            text="Hello world.",
            speaker="Alice",
            language="en",
        )
        assert s.speaker == "Alice"
        assert s.start_time == 0.0


class TestTranscriptResponse:
    def test_segment_count(self):
        r = TranscriptResponse(
            meeting_id=1,
            platform="google_meet",
            native_meeting_id="abc",
            status="completed",
            segments=[
                TranscriptSegmentResponse(start_time=0.0, end_time=3.0, text="Hi."),
                TranscriptSegmentResponse(start_time=3.0, end_time=6.0, text="Bye."),
            ],
            segment_count=2,
        )
        assert r.segment_count == 2
        assert len(r.segments) == 2


# ─────────────────────────────────────────────────────────────
# Webhook payloads
# ─────────────────────────────────────────────────────────────

class TestVexaStatusChangeEvent:
    def test_parses_status_change(self):
        payload = {
            "event": "meeting.status_change",
            "meeting": {
                "id": 127,
                "platform": "google_meet",
                "native_meeting_id": "abc-defg-hij",
                "status": "completed",
                "start_time": "2026-02-15T09:11:56.052175",
                "end_time": "2026-02-15T09:16:19.607242",
                "data": {"completion_reason": "stopped"},
            },
        }
        e = VexaStatusChangeEvent.model_validate(payload)
        assert e.meeting_id == 127
        assert e.status == "completed"
        assert e.platform == "google_meet"

    def test_alias_freeze(self):
        payload = {
            "event": "meeting.status_change",
            "meeting": {
                "id": 1,
                "platform": "teams",
                "native_meeting_id": "123",
                "status": "active",
                "start_time": None,
                "end_time": None,
                "data": {},
            },
        }
        e = VexaStatusChangeEvent.model_validate(payload)
        assert e.start_time is None


class TestVexaRecordingCompletedEvent:
    def test_parses_recording(self):
        payload = {
            "event": "recording.completed",
            "recording": {
                "id": 42,
                "meeting_id": 127,
                "platform": "google_meet",
                "native_meeting_id": "abc",
                "duration_seconds": 300,
                "url": "https://storage.vexa.ai/rec/42.mp4",
                "status": "completed",
            },
        }
        e = VexaRecordingCompletedEvent.model_validate(payload)
        assert e.recording_id == 42
        assert e.duration_seconds == 300


class TestWebhookResponse:
    def test_default(self):
        r = WebhookResponse()
        assert r.ok is True
        assert r.message == "Received"
