"""
Tests for app/services/vexa_client.py
Uses unittest.mock.patch to avoid real network calls.
"""

import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.services.vexa_client import (
    BotResponse,
    BotsStatusResponse,
    ConfigUpdateResponse,
    CreateBotRequest,
    DeleteBotResponse,
    MeetingRef,
    MeetingsListResponse,
    RecordingRef,
    ShareTranscriptResponse,
    TranscriptResponse,
    TranscriptSegment,
    UpdateBotConfigRequest,
    VexaClient,
)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

class AsyncMockResponse:
    """Fake httpx.Response."""

    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=self,
            )

    def json(self):
        return self._json


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return VexaClient(api_key="test-key-123", base_url="https://api.cloud.vexa.ai")


def make_mock_get(body: dict, status: int = 200):
    m = AsyncMock()
    m.return_value = AsyncMockResponse(status, body)
    return m


def make_mock_post(body: dict, status: int = 201):
    m = AsyncMock()
    m.return_value = AsyncMockResponse(status, body)
    return m


def make_mock_put(body: dict, status: int = 202):
    m = AsyncMock()
    m.return_value = AsyncMockResponse(status, body)
    return m


def make_mock_delete(body: dict, status: int = 200):
    m = AsyncMock()
    m.return_value = AsyncMockResponse(status, body)
    return m


# ─────────────────────────────────────────────────────────────
# Request model tests
# ─────────────────────────────────────────────────────────────

class TestCreateBotRequest:
    def test_defaults(self):
        req = CreateBotRequest(platform="google_meet", native_meeting_id="abc-defg-hij")
        assert req.platform == "google_meet"
        assert req.native_meeting_id == "abc-defg-hij"
        assert req.transcribe_enabled is True
        assert req.recording_enabled is False
        assert req.transcription_tier == "realtime"
        assert req.voice_agent_enabled is False
        assert req.passcode is None

    def test_all_fields(self):
        req = CreateBotRequest(
            platform="teams",
            native_meeting_id="1234567890123",
            passcode="XYZPASS",
            language="es",
            bot_name="Meety",
            recording_enabled=True,
            transcribe_enabled=True,
            transcription_tier="deferred",
        )
        d = req.model_dump(exclude_none=True)
        assert d["passcode"] == "XYZPASS"
        assert d["language"] == "es"
        assert d["bot_name"] == "Meety"
        assert d["transcription_tier"] == "deferred"

    def test_exclude_none(self):
        req = CreateBotRequest(platform="zoom", native_meeting_id="999")
        d = req.model_dump(exclude_none=True)
        assert "passcode" not in d
        assert "language" not in d


# ─────────────────────────────────────────────────────────────
# Bot lifecycle — create_bot
# ─────────────────────────────────────────────────────────────

class TestCreateBot:
    @pytest.mark.asyncio
    async def test_google_meet(self, client):
        mock_body = {
            "id": 219,
            "user_id": 4,
            "platform": "google_meet",
            "native_meeting_id": "abc-defg-hij",
            "constructed_meeting_url": "https://meet.google.com/abc-defg-hij",
            "status": "requested",
            "bot_container_id": "d21c5b0c5275c9fe9333",
            "start_time": None,
            "end_time": None,
            "data": {},
            "created_at": "2026-02-16T17:42:33.524137",
            "updated_at": "2026-02-16T17:42:33.535113",
        }

        async def mock_post(*args, **kwargs):
            return AsyncMockResponse(201, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.post = mock_post
            MockClient.return_value = instance

            result = await client.create_bot(
                CreateBotRequest(platform="google_meet", native_meeting_id="abc-defg-hij")
            )

        assert result.id == 219
        assert result.status == "requested"
        assert result.platform == "google_meet"

    @pytest.mark.asyncio
    async def test_teams_with_passcode(self, client):
        mock_body = {
            "id": 220,
            "user_id": 4,
            "platform": "teams",
            "native_meeting_id": "1234567890123",
            "constructed_meeting_url": "https://teams.live.com/meet/1234567890123",
            "status": "requested",
            "bot_container_id": None,
            "start_time": None,
            "end_time": None,
            "data": {},
            "created_at": "2026-02-16T18:00:00.000000",
            "updated_at": "2026-02-16T18:00:00.000000",
        }

        captured_body = {}

        async def mock_post(url, *, json, headers, **kw):
            captured_body.update(json)
            return AsyncMockResponse(201, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.post = mock_post
            MockClient.return_value = instance

            result = await client.create_bot(
                CreateBotRequest(
                    platform="teams",
                    native_meeting_id="1234567890123",
                    passcode="XYZPASS",
                    language="en",
                )
            )

        assert result.platform == "teams"
        assert captured_body["passcode"] == "XYZPASS"
        assert captured_body["language"] == "en"


# ─────────────────────────────────────────────────────────────
# Bot lifecycle — get_bots_status
# ─────────────────────────────────────────────────────────────

class TestGetBotsStatus:
    @pytest.mark.asyncio
    async def test_returns_running_bots(self, client):
        mock_body = {
            "running_bots": [
                {
                    "container_id": "abc123",
                    "container_name": "vexa-bot-219-fd0a58fb",
                    "platform": "google_meet",
                    "native_meeting_id": "abc-defg-hij",
                    "status": "Up 4 seconds",
                    "normalized_status": "Up",
                    "created_at": "2026-02-16T17:42:33+00:00",
                    "labels": {"vexa.user_id": "4"},
                    "meeting_id_from_name": "219",
                }
            ]
        }

        async def mock_get(*args, **kwargs):
            return AsyncMockResponse(200, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.get = mock_get
            MockClient.return_value = instance

            result = await client.get_bots_status()

        assert len(result.running_bots) == 1
        assert result.running_bots[0].normalized_status == "Up"
        assert result.running_bots[0].platform == "google_meet"

    @pytest.mark.asyncio
    async def test_empty_list(self, client):
        async def mock_get(*args, **kwargs):
            return AsyncMockResponse(200, {"running_bots": []})

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.get = mock_get
            MockClient.return_value = instance

            result = await client.get_bots_status()

        assert result.running_bots == []


# ─────────────────────────────────────────────────────────────
# Bot lifecycle — update_bot_config
# ─────────────────────────────────────────────────────────────

class TestUpdateBotConfig:
    @pytest.mark.asyncio
    async def test_update_language(self, client):
        captured_url = None

        async def mock_put(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return AsyncMockResponse(202, {"message": "Reconfiguration request accepted"})

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.put = mock_put
            MockClient.return_value = instance

            result = await client.update_bot_config(
                "google_meet",
                "abc-defg-hij",
                UpdateBotConfigRequest(language="es"),
            )

        assert result.message == "Reconfiguration request accepted"
        assert captured_url.endswith("/bots/google_meet/abc-defg-hij/config")


# ─────────────────────────────────────────────────────────────
# Bot lifecycle — remove_bot
# ─────────────────────────────────────────────────────────────

class TestRemoveBot:
    @pytest.mark.asyncio
    async def test_delete(self, client):
        captured_url = None

        async def mock_delete(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return AsyncMockResponse(200, {"message": "Bot stopped and removed"})

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.delete = mock_delete
            MockClient.return_value = instance

            result = await client.remove_bot("google_meet", "abc-defg-hij")

        assert "removed" in result.message.lower() or "stopped" in result.message.lower()
        assert "google_meet" in captured_url


# ─────────────────────────────────────────────────────────────
# Transcripts — get_transcript
# ─────────────────────────────────────────────────────────────

class TestGetTranscript:
    @pytest.mark.asyncio
    async def test_completed_transcript(self, client):
        mock_body = {
            "id": 129,
            "platform": "google_meet",
            "native_meeting_id": "zqe-gfmd-knr",
            "constructed_meeting_url": "https://meet.google.com/zqe-gfmd-knr",
            "status": "completed",
            "start_time": "2026-02-15T09:20:02.597046",
            "end_time": None,
            "recordings": [],
            "notes": None,
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": 3.2,
                    "text": "Hello everyone.",
                    "language": "en",
                    "created_at": "2026-02-15T09:20:20.123456",
                    "speaker": "Alex",
                    "completed": True,
                    "absolute_start_time": "2026-02-15T09:20:20.123456",
                    "absolute_end_time": "2026-02-15T09:20:23.323456",
                },
                {
                    "start_time": 3.2,
                    "end_time": 7.5,
                    "text": "Let's start with the agenda.",
                    "language": "en",
                    "created_at": "2026-02-15T09:20:23.323456",
                    "speaker": "Maria",
                    "completed": True,
                    "absolute_start_time": "2026-02-15T09:20:23.323456",
                    "absolute_end_time": "2026-02-15T09:20:27.623456",
                },
            ],
        }

        async def mock_get(*args, **kwargs):
            return AsyncMockResponse(200, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.get = mock_get
            MockClient.return_value = instance

            result = await client.get_transcript("google_meet", "zqe-gfmd-knr")

        assert result.id == 129
        assert result.status == "completed"
        assert len(result.segments) == 2
        assert result.segments[0].speaker == "Alex"
        assert result.segments[1].text == "Let's start with the agenda."

    @pytest.mark.asyncio
    async def test_segments_are_ordered(self, client):
        """Segments should preserve order from the API."""
        segments = [
            {"start_time": 0.0, "end_time": 5.0, "text": "First.", "speaker": "A", "completed": True},
            {"start_time": 5.0, "end_time": 10.0, "text": "Second.", "speaker": "B", "completed": True},
            {"start_time": 10.0, "end_time": 15.0, "text": "Third.", "speaker": "A", "completed": True},
        ]
        mock_body = {
            "id": 1,
            "platform": "zoom",
            "native_meeting_id": "999",
            "constructed_meeting_url": "https://zoom.us/j/999",
            "status": "completed",
            "segments": segments,
        }

        async def mock_get(*args, **kwargs):
            return AsyncMockResponse(200, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.get = mock_get
            MockClient.return_value = instance

            result = await client.get_transcript("zoom", "999")

        assert [s.text for s in result.segments] == ["First.", "Second.", "Third."]


# ─────────────────────────────────────────────────────────────
# Transcripts — share_transcript
# ─────────────────────────────────────────────────────────────

class TestShareTranscript:
    @pytest.mark.asyncio
    async def test_share_url_generated(self, client):
        mock_body = {
            "share_id": "Q-_Hyq3iOUi_H9C-XJEFrQ",
            "url": "https://api.vexa.ai/public/transcripts/Q-_Hyq3iOUi_H9C-XJEFrQ.txt",
            "expires_at": "2026-02-16T17:57:17.200672Z",
            "expires_in_seconds": 900,
        }

        async def mock_post(*args, **kwargs):
            return AsyncMockResponse(200, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.post = mock_post
            MockClient.return_value = instance

            result = await client.share_transcript("google_meet", "abc-defg-hij")

        assert result.share_id == "Q-_Hyq3iOUi_H9C-XJEFrQ"
        assert result.expires_in_seconds == 900


# ─────────────────────────────────────────────────────────────
# Meetings — list_meetings
# ─────────────────────────────────────────────────────────────

class TestListMeetings:
    @pytest.mark.asyncio
    async def test_returns_meetings(self, client):
        mock_body = {
            "meetings": [
                {
                    "id": 127,
                    "user_id": 4,
                    "platform": "google_meet",
                    "native_meeting_id": "zqe-gfmd-knr",
                    "constructed_meeting_url": "https://meet.google.com/zqe-gfmd-knr",
                    "status": "completed",
                    "bot_container_id": "vexa-bot-127-e76c2a06",
                    "start_time": "2026-02-15T09:11:56.052175",
                    "end_time": "2026-02-15T09:16:19.607242",
                    "data": {"completion_reason": "stopped"},
                    "created_at": "2026-02-15T09:11:30.287878",
                    "updated_at": "2026-02-15T09:16:19.606511",
                }
            ]
        }

        async def mock_get(*args, **kwargs):
            return AsyncMockResponse(200, mock_body)

        with patch("app.services.vexa_client.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.get = mock_get
            MockClient.return_value = instance

            result = await client.list_meetings()

        assert len(result.meetings) == 1
        assert result.meetings[0].id == 127
        assert result.meetings[0].status == "completed"


# ─────────────────────────────────────────────────────────────
# Response model validation
# ─────────────────────────────────────────────────────────────

class TestResponseModels:
    def test_bot_response_full(self):
        data = {
            "id": 1,
            "user_id": 4,
            "platform": "google_meet",
            "native_meeting_id": "abc",
            "constructed_meeting_url": "https://meet.google.com/abc",
            "status": "active",
            "bot_container_id": "container-xyz",
            "start_time": "2026-05-07T10:00:00Z",
            "end_time": None,
            "data": {"key": "value"},
            "created_at": "2026-05-07T09:59:00Z",
            "updated_at": "2026-05-07T10:00:00Z",
        }
        r = BotResponse.model_validate(data)
        assert r.status == "active"
        assert r.bot_container_id == "container-xyz"

    def test_recording_ref_minimal(self):
        r = RecordingRef(id=1, platform="google_meet", native_meeting_id="abc")
        assert r.duration_seconds is None
        assert r.url is None

    def test_transcript_segment_minimal(self):
        s = TranscriptSegment(start_time=0.0, end_time=3.0, text="Hi.")
        assert s.speaker is None
        assert s.language is None
        assert s.completed is True
