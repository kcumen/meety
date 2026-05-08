"""
Meetings router — /meetings/* endpoints.
Handles: join, list, status, summary, transcript, delete.
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db import get_db

logger = logging.getLogger("meety")


@contextmanager
def _db_ctx():
    """Context manager for use in background tasks / non-request code."""
    gen = get_db()
    try:
        db = next(gen)
        yield db
        db.commit()
    except StopIteration:
        pass
    finally:
        gen.close()

from app.db import (
    create_meeting,
    get_meeting_by_platform_id,
    store_transcript,
    update_meeting_summary,
)
from app.models import (
    JoinMeetingRequest,
    JoinMeetingResponse,
    MeetingListResponse,
    MeetingResponse,
    MeetingStatusResponse,
    MeetingSummary,
    MeetingSummaryResponse,
    TranscriptResponse,
    TranscriptSegmentResponse,
    UpdateMeetingRequest,
)
from app.services.url_parser import ParseError, parse
from app.services.vexa_client import CreateBotRequest, VexaClient

router = APIRouter(tags=["meetings"])


def _vexa() -> VexaClient:
    return VexaClient()


def _meeting_to_response(m) -> MeetingResponse:
    """Convert a Meeting ORM object to MeetingResponse."""
    return MeetingResponse(
        id=m.id,
        platform=m.platform,
        native_meeting_id=m.native_meeting_id,
        vexa_meeting_id=m.vexa_meeting_id,
        meeting_url=m.meeting_url,
        status=m.status,
        language=m.language,
        bot_name=m.bot_name,
        start_time=m.start_time,
        end_time=m.end_time,
        has_summary=m.summary is not None,
        has_transcript=m.transcript is not None,
        notes=m.notes,
        telegram_notify=bool(m.telegram_notify),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


# ── POST /meetings/join ──────────────────────────────────────────────────────

@router.post("/join", response_model=JoinMeetingResponse)
async def join_meeting(
    body: JoinMeetingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Parse the meeting URL, create a local record, and dispatch a vexa.ai bot.
    Returns immediately with the local meeting ID and vexa bot ID.
    """
    # 1 — parse URL
    try:
        parsed = parse(str(body.url))
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2 — check for duplicate
    existing = get_meeting_by_platform_id(db, parsed.platform, parsed.native_meeting_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Meeting {parsed.platform}/{parsed.native_meeting_id} already exists (id={existing.id})",
        )

    # 3 — create local record
    meeting = create_meeting(
        db,
        platform=parsed.platform,
        native_meeting_id=parsed.native_meeting_id,
        meeting_url=str(parsed.meeting_url),
        language=body.language,
        bot_name=body.bot_name,
        telegram_notify=1 if body.notify_telegram else 0,
    )
    db.commit()

    # 4 — dispatch bot to vexa (async — fire and forget with background task)
    background_tasks.add_task(_dispatch_bot, meeting.id, parsed, body)

    return JoinMeetingResponse(
        id=meeting.id,
        platform=parsed.platform,
        native_meeting_id=parsed.native_meeting_id,
        vexa_bot_id=0,  # updated once vexa responds
        status="requested",
        meeting_url=str(parsed.meeting_url),
    )


async def _dispatch_bot(meeting_id: int, parsed, body: JoinMeetingRequest):
    """Background task: create bot in vexa, update local record with vexa IDs."""
    vexa = _vexa()
    req = CreateBotRequest(
        platform=parsed.platform,
        native_meeting_id=parsed.native_meeting_id,
        passcode=parsed.passcode,
        language=body.language,
        bot_name=body.bot_name,
        task=body.task,
        voice_agent_enabled=body.voice_agent_enabled,
        recording_enabled=body.recording_enabled,
        transcribe_enabled=body.transcribe_enabled,
        transcription_tier=body.transcription_tier,
    )
    try:
        bot = await vexa.create_bot(req)
        # Update local record with vexa IDs
        with _db_ctx() as db:
            from app.db import Meeting
            m = db.get(Meeting, meeting_id)
            if m:
                m.vexa_meeting_id = bot.id
                m.status = bot.status
                db.commit()
    except Exception as exc:
        # Log but don't crash — bot creation can be retried
        import logging

        logging.getLogger("meety").error(f"Bot dispatch failed for meeting {meeting_id}: {exc}")
        with _db_ctx() as db:
            from app.db import Meeting
            m = db.get(Meeting, meeting_id)
            if m:
                m.status = "failed"
                db.commit()


# ── GET /meetings ────────────────────────────────────────────────────────────

@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all meetings, newest first."""
    from app.db import Meeting

    total = db.query(Meeting).count()
    rows = (
        db.query(Meeting)
        .order_by(Meeting.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return MeetingListResponse(
        meetings=[_meeting_to_response(m) for m in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


# ── GET /meetings/{id} (numeric DB id) ───────────────────────────────────────

@router.get("/{meeting_id:int}", response_model=MeetingResponse)
async def get_meeting_by_id(
    meeting_id: int,
    db: Session = Depends(get_db),
):
    """Get a single meeting by its numeric database ID (used by web UI polling)."""
    from app.db import Meeting
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _meeting_to_response(m)


# ── GET /meetings/{platform}/{native_meeting_id} ─────────────────────────────

@router.get("/{platform}/{native_meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """Get a single meeting by its platform identity."""
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _meeting_to_response(m)


# ── GET /meetings/{platform}/{native_meeting_id}/status ──────────────────────

@router.get("/{platform}/{native_meeting_id}/status", response_model=MeetingStatusResponse)
async def get_meeting_status(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """
    Real-time status via polling.
    First checks local DB, then refreshes from vexa /bots/status.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Count segments collected so far
    segment_count = 0
    if m.transcript:
        segment_count = m.transcript.segment_count or 0

    # If local status is stale (still requested/joining/active), check vexa
    if m.status in ("requested", "joining", "active"):
        try:
            vexa = _vexa()
            status_resp = await vexa.get_bots_status(
                platform=platform, native_meeting_id=native_meeting_id
            )
            if status_resp.running_bots:
                bot = status_resp.running_bots[0]
                m.status = bot.normalized_status or bot.status
                db.commit()
        except Exception:
            pass  # stay with local status on vexa errors

    return MeetingStatusResponse(
        status=m.status,
        start_time=m.start_time,
        end_time=m.end_time,
        segments_so_far=segment_count,
        vexa_bot_id=m.vexa_meeting_id,
    )



# ── GET /meetings/{meeting_id}/summary (numeric ID) ────────────────────────────
# NOTE: using str path param + int() conversion to avoid Starlette routing bug
# where /{meeting_id:int}/summary gets shadowed by /{platform}/{native}/summary

@router.get("/{meeting_id}/summary", response_model=MeetingSummaryResponse)
async def get_meeting_summary_by_id(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    """Return the AI-generated summary by numeric meeting ID (used by web UI)."""
    try:
        numeric_id = int(meeting_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    from app.db import Meeting
    m = db.get(Meeting, numeric_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if m.summary is None:
        return MeetingSummaryResponse(
            meeting_id=m.id,
            platform=m.platform,
            native_meeting_id=m.native_meeting_id,
            summary=None,
            summary_text=None,
        )

    try:
        data = json.loads(m.summary)
        summary = MeetingSummary.model_validate(data)
    except Exception:
        return MeetingSummaryResponse(
            meeting_id=m.id,
            platform=m.platform,
            native_meeting_id=m.native_meeting_id,
            summary=None,
            summary_text=m.summary,
        )

    return MeetingSummaryResponse(
        meeting_id=m.id,
        platform=m.platform,
        native_meeting_id=m.native_meeting_id,
        summary=summary,
        summary_text=None,
    )


# ── GET /meetings/{platform}/{native_meeting_id}/summary ─────────────────────

@router.get("/{platform}/{native_meeting_id}/summary", response_model=MeetingSummaryResponse)
async def get_meeting_summary(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """Return the AI-generated summary by numeric meeting ID (used by web UI)."""
    # FastAPI/Starlette routes /meetings/{id}/summary here due to segment-count
    # priority — redirect to the typed endpoint when platform is a number.
    if platform.isdigit():
        return await get_meeting_summary_by_id(int(platform), db)
    """Return the AI-generated summary, if available."""
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if m.summary is None:
        return MeetingSummaryResponse(
            meeting_id=m.id,
            platform=platform,
            native_meeting_id=native_meeting_id,
            summary=None,
            summary_text=None,
        )

    try:
        data = json.loads(m.summary)
        summary = MeetingSummary.model_validate(data)
    except Exception:
        # Parsing failed — return raw text
        return MeetingSummaryResponse(
            meeting_id=m.id,
            platform=platform,
            native_meeting_id=native_meeting_id,
            summary=None,
            summary_text=m.summary,
        )

    return MeetingSummaryResponse(
        meeting_id=m.id,
        platform=platform,
        native_meeting_id=native_meeting_id,
        summary=summary,
        summary_text=None,
    )

# ── GET /meetings/{platform}/{native_meeting_id}/transcript ──────────────────

@router.get("/{platform}/{native_meeting_id}/transcript", response_model=TranscriptResponse)
async def get_meeting_transcript(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the transcript for a meeting.
    If not yet stored locally, fetches it from vexa and stores it.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if m.transcript is None:
        # Lazy fetch from vexa
        vexa = _vexa()
        try:
            tx = await vexa.get_transcript(platform, native_meeting_id)
            segments_dicts = [s.model_dump() for s in tx.segments]
            raw = json.dumps(tx.model_dump())
            with _db_ctx() as inner_db:
                stored = store_transcript(inner_db, m.id, segments_dicts, raw)
                inner_db.commit()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Vexa transcript fetch failed: {e}")
    else:
        segments_dicts = json.loads(m.transcript.segments or "[]")
        raw = m.transcript.raw_json or "{}"

    # Parse for response
    start_time = None
    end_time = None
    status = m.status
    if raw and raw != "{}":
        try:
            tx_data = json.loads(raw)
            start_time = tx_data.get("start_time")
            end_time = tx_data.get("end_time")
        except Exception:
            pass

    return TranscriptResponse(
        meeting_id=m.id,
        platform=platform,
        native_meeting_id=native_meeting_id,
        status=status,
        start_time=datetime.fromisoformat(start_time.replace("Z", "+00:00")) if start_time else None,
        end_time=datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None,
        segments=[TranscriptSegmentResponse.model_validate(s) for s in segments_dicts],
        segment_count=len(segments_dicts),
    )


# ── DELETE /meetings/{platform}/{native_meeting_id} ──────────────────────────

@router.delete("/{platform}/{native_meeting_id}")
async def delete_meeting(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """
    Stop the vexa bot, delete vexa artifacts, and remove the local record.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting_id = m.id
    status = m.status

    # Deep delete in vexa if finalized, else just stop the bot
    try:
        vexa = _vexa()
        if status in ("completed", "failed"):
            await vexa.delete_meeting(platform, native_meeting_id)
        else:
            await vexa.remove_bot(platform, native_meeting_id)
    except Exception:
        pass  # proceed with local deletion

    # Delete local record (cascades to transcript)
    db.delete(m)
    db.commit()

    return Response(status_code=204)


# ── POST /meetings/{platform}/{native_meeting_id}/stop ───────────────────────

@router.post("/{platform}/{native_meeting_id}/stop")
async def stop_meeting_bot(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """
    Tells vexa to remove the bot from the meeting.
    The local status will be updated via webhook later.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        from app.services.vexa_client import VexaClient
        vexa = VexaClient()
        await vexa.remove_bot(platform, native_meeting_id)
        return {"ok": True, "message": "Stop request sent to Vexa"}
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


# ── PATCH /meetings/{platform}/{native_meeting_id} ──────────────────────────

@router.patch("/{platform}/{native_meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    platform: str,
    native_meeting_id: str,
    body: UpdateMeetingRequest,
    db: Session = Depends(get_db),
):
    """
    Update local meeting notes and sync them with Vexa.ai.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Update local
    if body.notes is not None:
        m.notes = body.notes
    db.commit()

    # Sync with Vexa (optional/best-effort)
    try:
        vexa = _vexa()
        # Vexa expects data: { notes: "..." }
        await vexa.patch_meeting(platform, native_meeting_id, {"notes": body.notes})
    except Exception as e:
        logger.warning(f"Failed to sync notes with Vexa: {e}")

    return _meeting_to_response(m)


# ── POST /meetings/{platform}/{native_meeting_id}/share ──────────────────────

@router.post("/{platform}/{native_meeting_id}/share")
async def share_meeting_transcript(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    """
    Generate a temporary public share link for the transcript via Vexa.
    """
    m = get_meeting_by_platform_id(db, platform, native_meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        vexa = _vexa()
        share_data = await vexa.share_transcript(platform, native_meeting_id)
        return share_data.model_dump()
    except Exception as e:
        logger.error(f"Failed to share transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate share link: {str(e)}")


# ── GET /meetings/events (SSE) ────────────────────────────────────────────────

@router.get("/events")
async def meeting_events():
    """
    Server-Sent Events endpoint for real-time UI updates.
    The UI connects here and waits for notifications from the webhook handler.
    """
    from app.services.notifier import notifier
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        notifier.subscribe(),
        media_type="text/event-stream"
    )
