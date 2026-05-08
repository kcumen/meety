"""
Vexa.ai API client.
Covers: bot lifecycle, transcripts, and config updates.
https://docs.vexa.ai/api/bots
https://docs.vexa.ai/api/transcripts
https://docs.vexa.ai/api/meetings
"""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field

from app.config import settings

# ─────────────────────────────────────────────────────────────
# Models — request payloads
# ─────────────────────────────────────────────────────────────

class CreateBotRequest(BaseModel):
    """Payload for POST /bots."""
    platform: str = Field(description="google_meet | teams | zoom")
    native_meeting_id: str
    passcode: str | None = None
    language: str | None = None
    task: str | None = Field(default="transcribe", description="transcribe | translate")
    bot_name: str | None = None
    recording_enabled: bool = False
    transcribe_enabled: bool = True
    transcription_tier: str | None = Field(
        default="realtime",
        description="realtime | deferred",
    )
    voice_agent_enabled: bool = False


class UpdateBotConfigRequest(BaseModel):
    """Payload for PUT /bots/{platform}/{native_meeting_id}/config."""
    language: str | None = None
    task: str | None = None


# ─────────────────────────────────────────────────────────────
# Models — API responses
# ─────────────────────────────────────────────────────────────

class BotResponse(BaseModel):
    """Response from POST /bots (201)."""
    id: int
    user_id: int
    platform: str
    native_meeting_id: str
    constructed_meeting_url: str
    status: str
    bot_container_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    data: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class RunningBot(BaseModel):
    """A single bot entry from GET /bots/status."""
    container_id: str
    container_name: str | None = None
    platform: str
    native_meeting_id: str
    status: str
    normalized_status: str | None = None
    created_at: str
    labels: dict = Field(default_factory=dict)
    meeting_id_from_name: str | None = None


class BotsStatusResponse(BaseModel):
    """Response from GET /bots/status."""
    running_bots: list[RunningBot] = Field(default_factory=list)


class ConfigUpdateResponse(BaseModel):
    """Response from PUT /bots/{platform}/{native_meeting_id}/config (202)."""
    message: str


class DeleteBotResponse(BaseModel):
    """Response from DELETE /bots/{platform}/{native_meeting_id}."""
    message: str


class TranscriptSegment(BaseModel):
    """A single utterance in a transcript."""
    start_time: float
    end_time: float
    text: str
    language: str | None = None
    created_at: str | None = None
    speaker: str | None = None
    completed: bool = True
    absolute_start_time: str | None = None
    absolute_end_time: str | None = None


class RecordingRef(BaseModel):
    """Reference to a recording artifact."""
    id: int
    platform: str
    native_meeting_id: str
    duration_seconds: int | None = None
    status: str | None = None
    url: str | None = None
    created_at: str | None = None


class TranscriptResponse(BaseModel):
    """Response from GET /transcripts/{platform}/{native_meeting_id}."""
    id: int
    platform: str
    native_meeting_id: str
    constructed_meeting_url: str
    status: str
    start_time: str | None = None
    end_time: str | None = None
    recordings: list[RecordingRef] = Field(default_factory=list)
    notes: str | None = None
    segments: list[TranscriptSegment] = Field(default_factory=list)


class ShareTranscriptResponse(BaseModel):
    """Response from POST /transcripts/{platform}/{native_meeting_id}/share."""
    share_id: str
    url: str
    expires_at: str
    expires_in_seconds: int


class MeetingRef(BaseModel):
    """A meeting entry from GET /meetings."""
    id: int
    user_id: int
    platform: str
    native_meeting_id: str
    constructed_meeting_url: str
    status: str
    bot_container_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    data: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class MeetingsListResponse(BaseModel):
    """Response from GET /meetings."""
    meetings: list[MeetingRef] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────

class VexaClient:
    """
    Thin async client for vexa.ai REST API.

    All methods carry the X-API-Key header automatically.
    Base URL is read from settings.VEXA_API_BASE (defaults to
    https://api.cloud.vexa.ai if not set).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or settings.VEXA_API_KEY
        self.base_url = (base_url or settings.VEXA_API_BASE or "https://api.cloud.vexa.ai").rstrip(
            "/"
        )
        self.timeout = timeout

    # ── Bot lifecycle ────────────────────────────────────────

    async def create_bot(self, request: CreateBotRequest) -> BotResponse:
        """
        POST /bots
        Creates a bot and returns the created bot record.
        Raises httpx.HTTPStatusError on non-2xx responses.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/bots",
                json=request.model_dump(exclude_none=True),
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return BotResponse.model_validate(resp.json())

    async def get_bots_status(
        self, platform: str | None = None, native_meeting_id: str | None = None
    ) -> BotsStatusResponse:
        """
        GET /bots/status
        Lists all running bots. Optionally filter by platform / meeting ID.
        """
        params: dict[str, str] = {}
        if platform:
            params["platform"] = platform
        if native_meeting_id:
            params["native_meeting_id"] = native_meeting_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/bots/status",
                params=params,
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return BotsStatusResponse.model_validate(resp.json())

    async def update_bot_config(
        self,
        platform: str,
        native_meeting_id: str,
        request: UpdateBotConfigRequest,
    ) -> ConfigUpdateResponse:
        """
        PUT /bots/{platform}/{native_meeting_id}/config
        Updates language / task on a running bot.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.put(
                f"{self.base_url}/bots/{platform}/{native_meeting_id}/config",
                json=request.model_dump(exclude_none=True),
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return ConfigUpdateResponse.model_validate(resp.json())

    async def remove_bot(self, platform: str, native_meeting_id: str) -> DeleteBotResponse:
        """
        DELETE /bots/{platform}/{native_meeting_id}
        Stops and removes the bot from the meeting.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(
                f"{self.base_url}/bots/{platform}/{native_meeting_id}",
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return DeleteBotResponse.model_validate(resp.json())

    async def delete_meeting(self, platform: str, native_meeting_id: str) -> dict:
        """
        DELETE /meetings/{platform}/{native_meeting_id}
        Anonymizes the meeting and deletes transcript/recording artifacts.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(
                f"{self.base_url}/meetings/{platform}/{native_meeting_id}",
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return resp.json()

    # ── Transcripts ───────────────────────────────────────────

    async def get_transcript(
        self, platform: str, native_meeting_id: str
    ) -> TranscriptResponse:
        """
        GET /transcripts/{platform}/{native_meeting_id}
        Fetches the full transcript with segments and speaker info.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/transcripts/{platform}/{native_meeting_id}",
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return TranscriptResponse.model_validate(resp.json())

    async def share_transcript(
        self, platform: str, native_meeting_id: str, ttl_seconds: int = 900
    ) -> ShareTranscriptResponse:
        """
        POST /transcripts/{platform}/{native_meeting_id}/share
        Creates a temporary public URL (default 15 min TTL).
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/transcripts/{platform}/{native_meeting_id}/share",
                params={"ttl_seconds": ttl_seconds},
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return ShareTranscriptResponse.model_validate(resp.json())

    # ── Meetings ───────────────────────────────────────────────

    async def patch_meeting(
        self, platform: str, native_meeting_id: str, data: dict
    ) -> MeetingRef:
        """
        PATCH /meetings/{platform}/{native_meeting_id}
        Updates meeting metadata (e.g., notes, name).
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.patch(
                f"{self.base_url}/meetings/{platform}/{native_meeting_id}",
                json={"data": data},
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return MeetingRef.model_validate(resp.json())


    async def list_meetings(
        self, limit: int = 50, offset: int = 0
    ) -> MeetingsListResponse:
        """
        GET /meetings
        Lists meeting history for the authenticated user.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/meetings",
                params={"limit": limit, "offset": offset},
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            return MeetingsListResponse.model_validate(resp.json())
