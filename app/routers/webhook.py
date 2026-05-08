"""
Webhook router — /webhook/vexa endpoint.
Handles vexa.ai event notifications: meeting.status_change, recording.completed.
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Request

from app.db import get_db
from app.models import (
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
      - meeting.started
      - meeting.completed
      - bot.failed
      - recording.completed

    Background tasks:
      - On 'completed': fetch transcript and trigger summarization
      - On 'recording.completed': store recording reference
      - All events: broadcast to connected Web UI clients
    """
    body = await request.json()
    event_type = body.get("event") or body.get("event_type") or ""
    logger.info(f"Webhook received: {event_type} | Body: {json.dumps(body)}")

    meeting_events = ["meeting.status_change", "meeting.started", "meeting.completed", "bot.failed"]

    if event_type in meeting_events:
        from app.models import VexaMeetingEvent
        from app.services.notifier import notifier

        try:
            event = VexaMeetingEvent.model_validate(body)
        except Exception as e:
            logger.warning(f"Invalid meeting event payload: {e} | body: {body}")
            return WebhookResponse(ok=False, message="Invalid payload")

        # Broadcast to UI
        background_tasks.add_task(notifier.broadcast, event_type, event.model_dump())
        
        # Handle core logic
        background_tasks.add_task(_handle_meeting_event, event)
        return WebhookResponse(ok=True, message="Accepted")

    elif event_type == "recording.completed":
        from app.models import VexaRecordingCompletedEvent
        from app.services.notifier import notifier

        try:
            event = VexaRecordingCompletedEvent.model_validate(body)
        except Exception:
            logger.warning(f"Invalid recording payload: {body}")
            return WebhookResponse(ok=False, message="Invalid payload")

        # Broadcast to UI
        background_tasks.add_task(notifier.broadcast, event_type, event.model_dump())
        
        background_tasks.add_task(_handle_recording_completed, event)
        return WebhookResponse(ok=True, message="Accepted")

    else:
        logger.info(f"Ignoring unknown webhook event: {event_type}")
        return WebhookResponse(ok=True, message=f"Ignored event type: {event_type}")


# ── Background handlers ───────────────────────────────────────────────────────

async def _handle_meeting_event(event):
    """
    On meeting events: update status, fetch transcript, generate summary.
    """
    from app.models import TranscriptSegmentResponse, VexaMeetingEvent
    from app.services.summarizer import generate_summary

    # Map events to status
    new_status = event.status
    if event.event == "meeting.started":
        new_status = "active"
    elif event.event == "meeting.completed":
        new_status = "completed"
    elif event.event == "bot.failed":
        new_status = "failed"

    if not new_status:
        return

    vexa = VexaClient()
    meeting_id: int | None = None
    meeting_language: str | None = None

    # 1. Update meeting status and timestamps
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

        meeting_id = m.id
        meeting_language = m.language
        m.status = new_status

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

    # 2. If completed, fetch transcript and generate summary
    if new_status == "completed":
        import asyncio
        await asyncio.sleep(10)  # Wait for Vexa to finalize transcript processing
        segments_dicts: list[dict] = []
        try:
            tx = await vexa.get_transcript(event.platform, event.native_meeting_id)
            segments_dicts = [s.model_dump() for s in tx.segments]

            with _db_ctx() as db2:
                from app.db import Meeting, Transcript

                # Ensure we delete any existing transcript to avoid IntegrityError
                db2.query(Transcript).filter(Transcript.meeting_id == meeting_id).delete()
                db2.commit()

                stored = Transcript(
                    meeting_id=meeting_id,
                    segments=json.dumps(segments_dicts),
                    raw_json=json.dumps(tx.model_dump(mode="json")),
                    segment_count=len(segments_dicts),
                )
                db2.add(stored)
                db2.commit()
        except Exception as e:
            logger.error(f"Transcript fetch failed: {e}")

        # 3. Generate summary via OpenRouter
        if meeting_id is not None:
            try:
                segs = [
                    TranscriptSegmentResponse(**s) for s in segments_dicts
                ]
                summary = await generate_summary(
                    segs,
                    meeting_id=meeting_id,
                    language=meeting_language,
                )

                # 4. Store summary in DB
                with _db_ctx() as db3:
                    from app.db import Meeting, update_meeting_summary
                    # Use mode="json" to ensure datetimes are serialized to strings
                    update_meeting_summary(db3, meeting_id, summary.model_dump(mode="json"))
                    logger.info(f"Summary generated for meeting {meeting_id}")
            except Exception as e:
                logger.error(f"Summarization failed for meeting {meeting_id}: {e}")


async def _handle_recording_completed(event):
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
