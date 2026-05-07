"""
Webhook router — /webhook/vexa endpoint.
Handles vexa.ai event notifications: meeting.status_change, recording.completed.
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Request

from app.db import get_db, store_transcript, update_meeting_summary
from app.models import (
    MeetingSummary,
    VexaRecordingCompletedEvent,
    VexaStatusChangeEvent,
    WebhookResponse,
)
from app.services.vexa_client import VexaClient

router = APIRouter(tags=["webhook"])
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


# ── POST /webhook/vexa ───────────────────────────────────────────────────────

@router.post("/vexa", response_model=WebhookResponse)
async def vexa_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives vexa.ai webhook events.
    Supported events:
      - meeting.status_change
      - recording.completed

    Background tasks:
      - On 'completed': fetch transcript and trigger summarization
      - On 'recording.completed': store recording reference
    """
    body = await request.json()
    event_type = body.get("event", "")

    if event_type == "meeting.status_change":
        try:
            event = VexaStatusChangeEvent.model_validate(body)
        except Exception:
            logger.warning(f"Invalid status_change payload: {body}")
            return WebhookResponse(ok=False, message="Invalid payload")

        background_tasks.add_task(_handle_status_change, event)
        return WebhookResponse(ok=True, message="Accepted")

    elif event_type == "recording.completed":
        try:
            event = VexaRecordingCompletedEvent.model_validate(body)
        except Exception:
            logger.warning(f"Invalid recording payload: {body}")
            return WebhookResponse(ok=False, message="Invalid payload")

        background_tasks.add_task(_handle_recording_completed, event)
        return WebhookResponse(ok=True, message="Accepted")

    else:
        logger.info(f"Ignoring unknown webhook event: {event_type}")
        return WebhookResponse(ok=True, message=f"Ignored event type: {event_type}")


# ── Background handlers ───────────────────────────────────────────────────────

async def _handle_status_change(event: VexaStatusChangeEvent):
    """
    On meeting completion: fetch transcript, generate summary.
    """
    if event.status != "completed":
        return

    vexa = VexaClient()

    with _db_ctx() as db:
        from app.db import Meeting

        m = db.query(Meeting).filter(
            Meeting.platform == event.platform,
            Meeting.native_meeting_id == event.native_meeting_id,
        ).first()

        if not m:
            logger.warning(
                f"Webhook: meeting not found "
                f"{event.platform}/{event.native_meeting_id}"
            )
            return

        # Update status and timestamps
        m.status = "completed"
        if event.start_time:
            try:
                m.start_time = datetime.fromisoformat(
                    event.start_time.replace("Z", "+00:00")
                )
            except Exception:
                pass
        if event.end_time:
            try:
                m.end_time = datetime.fromisoformat(
                    event.end_time.replace("Z", "+00:00")
                )
            except Exception:
                pass
        db.commit()

    # Fetch transcript
    try:
        tx = await vexa.get_transcript(event.platform, event.native_meeting_id)
        segments_dicts = [s.model_dump() for s in tx.segments]
        raw_json = json.dumps(tx.model_dump())

        with _db_ctx() as db2:
            from app.db import Meeting, Transcript

            # Remove existing if any
            existing = db2.query(Transcript).filter(
                Transcript.meeting_id == m.id
            ).first()
            if existing:
                db2.delete(existing)

            stored = Transcript(
                meeting_id=m.id,
                segments=json.dumps(segments_dicts),
                raw_json=raw_json,
                segment_count=len(segments_dicts),
            )
            db2.add(stored)
            db2.commit()
            segment_count = len(segments_dicts)
    except Exception as e:
        logger.error(f"Transcript fetch failed: {e}")
        segment_count = 0

    # Trigger summarization (placeholder — task 13 implements the actual LLM call)
    if segment_count > 0:
        background_tasks_add_summary_task(m.id, event.platform, event.native_meeting_id)


async def _handle_recording_completed(event: VexaRecordingCompletedEvent):
    """Store a recording reference on the meeting."""
    with _db_ctx() as db:
        from app.db import Meeting

        m = db.query(Meeting).filter(
            Meeting.platform == event.platform,
            Meeting.native_meeting_id == event.native_meeting_id,
        ).first()

        if not m:
            logger.warning(
                f"Recording webhook: meeting not found "
                f"{event.platform}/{event.native_meeting_id}"
            )
            return

        # TODO (v2): store recording reference in meeting.data or a recordings table
        logger.info(
            f"Recording completed for {event.platform}/{event.native_meeting_id}: "
            f"{event.duration_seconds}s — {event.url}"
        )
        db.commit()


def background_tasks_add_summary_task(meeting_id: int, platform: str, native_meeting_id: str):
    """
    Placeholder that task 13 will replace with real OpenRouter summarization.
    For now it stores a stub summary so the endpoint returns something meaningful.
    """
    # Import here to avoid circular imports
    from app.config import settings
    from app.db import get_db, Meeting

    stub_summary = {
        "executive_summary": "[Summary pending — OpenRouter integration coming soon]",
        "tasks": [],
        "commitments": [],
        "key_points": [],
        "next_meeting": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": None,
    }

    with _db_ctx() as db:
        m = db.get(Meeting, meeting_id)
        if m:
            m.summary = json.dumps(stub_summary)
            db.commit()
