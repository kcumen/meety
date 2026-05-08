"""
Pydantic schemas — request / response models for the FastAPI layer.
Covers: meetings join, status, summary, and webhook payloads.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator, HttpUrl


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class Platform(str, Enum):
    google_meet = "google_meet"
    teams = "teams"
    zoom = "zoom"


class MeetingStatus(str, Enum):
    requested = "requested"
    joining = "joining"
    active = "active"
    completed = "completed"
    failed = "failed"


# ─────────────────────────────────────────────────────────────
# Meeting — request
# ─────────────────────────────────────────────────────────────

class JoinMeetingRequest(BaseModel):
    """POST /meetings/join"""

    url: HttpUrl = Field(description="Meeting URL (Google Meet, Teams, or Zoom)")
    language: str | None = Field(
        default=None,
        max_length=8,
        description="Language code for transcription (e.g. 'en', 'es'). "
        "Defaults to auto-detect.",
    )
    bot_name: str | None = Field(
        default="KcuBot | kcumen.co",
        max_length=128,
        description="Display name of the bot in the meeting.",
    )
    transcribe_enabled: bool = Field(
        default=True, description="Enable transcription (default: true)"
    )
    recording_enabled: bool = Field(
        default=False, description="Enable recording (default: false)"
    )
    transcription_tier: str | None = Field(
        default="realtime",
        description="realtime | deferred (default: realtime)",
    )
    task: str | None = Field(
        default="transcribe",
        description="transcribe | translate (default: transcribe)",
    )
    voice_agent_enabled: bool = Field(
        default=False,
        description="Enable interactive voice agent capabilities.",
    )
    notify_telegram: bool = Field(
        default=True,
        description="Send a Telegram message when the summary is ready.",
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateMeetingRequest(BaseModel):
    """PATCH /meetings/{platform}/{native_meeting_id}"""
    notes: str | None = None


# ─────────────────────────────────────────────────────────────
# Meeting — response
# ─────────────────────────────────────────────────────────────

class MeetingResponse(BaseModel):
    """A meeting record returned by the API."""

    id: int
    platform: str
    native_meeting_id: str
    vexa_meeting_id: int | None = None
    meeting_url: str
    status: str
    language: str | None = None
    bot_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    has_summary: bool = False
    has_transcript: bool = False
    notes: str | None = None
    telegram_notify: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingListResponse(BaseModel):
    """Paginated list of meetings."""

    meetings: list[MeetingResponse]
    total: int
    limit: int
    offset: int


class JoinMeetingResponse(BaseModel):
    """Response from POST /meetings/join (201)."""

    id: int = Field(description="Local database ID")
    platform: str
    native_meeting_id: str
    vexa_bot_id: int = Field(description="Bot ID from vexa.ai")
    status: str
    meeting_url: str


# ─────────────────────────────────────────────────────────────
# Meeting — status (real-time polling)
# ─────────────────────────────────────────────────────────────

class MeetingStatusResponse(BaseModel):
    """GET /meetings/{platform}/{native_meeting_id}/status"""

    status: str = Field(description="requested | joining | active | completed | failed")
    start_time: datetime | None = None
    end_time: datetime | None = None
    segments_so_far: int = Field(default=0, description="Transcript segments collected so far")
    notes: str | None = None
    vexa_bot_id: int | None = None


# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

class TaskItem(BaseModel):
    """A task extracted from the meeting."""

    description: str
    assignee: str | None = None
    due: str | None = None  # YYYY-MM-DD or null
    priority: str | None = None  # high | medium | low


class CommitmentItem(BaseModel):
    """A commitment made during the meeting."""

    description: str
    by: str | None = None
    due: str | None = None  # YYYY-MM-DD or null


class MeetingSummary(BaseModel):
    """The full AI-generated summary."""

    executive_summary: str = Field(description="2-3 sentence executive summary")
    tasks: list[TaskItem] = Field(default_factory=list)
    commitments: list[CommitmentItem] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    next_meeting: str | None = None
    generated_at: datetime
    model: str | None = None


class MeetingSummaryResponse(BaseModel):
    """GET /meetings/{platform}/{native_meeting_id}/summary"""

    meeting_id: int
    platform: str
    native_meeting_id: str
    summary: MeetingSummary | None = None
    summary_text: str | None = Field(
        default=None,
        description="Raw summary text if structured parsing failed",
    )


# ─────────────────────────────────────────────────────────────
# Transcript
# ─────────────────────────────────────────────────────────────

class TranscriptSegmentResponse(BaseModel):
    """A single transcript segment."""

    start_time: float = Field(alias="start")
    end_time: float = Field(alias="end")
    text: str
    speaker: str | None = None
    language: str | None = None
    absolute_start_time: str | None = None
    absolute_end_time: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TranscriptResponse(BaseModel):
    """GET /meetings/{platform}/{native_meeting_id}/transcript"""

    meeting_id: int
    platform: str
    native_meeting_id: str
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    segments: list[TranscriptSegmentResponse]
    segment_count: int


# ─────────────────────────────────────────────────────────────
# Webhook payloads
# ─────────────────────────────────────────────────────────────

class VexaMeetingEvent(BaseModel):
    """Payload from vexa.ai for meeting related webhooks."""

    event: str = Field(description="meeting.status_change | meeting.started | meeting.completed | bot.failed")
    meeting_id: int = Field(description="Meeting ID from vexa")
    platform: str = Field(description="google_meet | teams | zoom")
    native_meeting_id: str = Field(description="Platform-specific meeting ID")
    status: str | None = Field(default=None, description="requested | joining | active | completed | failed")
    start_time: str | None = Field(default=None)
    end_time: str | None = Field(default=None)
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _extract_meeting(cls, values: dict) -> dict:
        """vexa.ai sends meeting data nested under 'meeting' or 'data.meeting' key — flatten it."""
        event_name = values.get("event") or values.get("event_type")
        
        # Look for meeting data in various possible locations
        m = values.get("meeting")
        if not m and isinstance(values.get("data"), dict):
            m = values["data"].get("meeting")
            
        if m and isinstance(m, dict):
            return {
                "event": event_name,
                "meeting_id": m.get("id"),
                "platform": m.get("platform"),
                "native_meeting_id": m.get("native_meeting_id"),
                "status": m.get("status"),
                "start_time": m.get("start_time"),
                "end_time": m.get("end_time"),
                "data": m.get("data", {}),
            }
        return {**values, "event": event_name}


class VexaRecordingCompletedEvent(BaseModel):
    """Payload from vexa.ai for recording.completed webhook."""

    event: str = "recording.completed"
    meeting_id: int = Field(description="Meeting ID from vexa")
    recording_id: int = Field(description="Recording ID from vexa")
    platform: str = Field(description="google_meet | teams | zoom")
    native_meeting_id: str = Field(description="Platform-specific meeting ID")
    duration_seconds: int | None = Field(default=None)
    url: str | None = Field(default=None)
    status: str | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _extract_recording(cls, values: dict) -> dict:
        """vexa.ai sends recording data nested under 'recording' key — flatten it."""
        if "recording" in values and isinstance(values["recording"], dict):
            r = values["recording"]
            return {
                "event": values.get("event"),
                "meeting_id": r.get("meeting_id"),
                "recording_id": r.get("id"),
                "platform": r.get("platform"),
                "native_meeting_id": r.get("native_meeting_id"),
                "duration_seconds": r.get("duration_seconds"),
                "url": r.get("url"),
                "status": r.get("status"),
            }
        return values


class WebhookResponse(BaseModel):
    """Generic webhook acknowledgement."""

    ok: bool = True
    message: str = "Received"


# ─────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    vexa_configured: bool = False
    openrouter_configured: bool = False
    database: str = "sqlite"
