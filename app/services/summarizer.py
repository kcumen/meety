"""
Summarizer service — generates AI meeting summaries via OpenRouter.

OpenRouter is OpenAI-compatible, so we use the standard /chat/completions endpoint.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.models import (
    CommitmentItem,
    MeetingSummary,
    TaskItem,
    TranscriptSegmentResponse,
)

logger = logging.getLogger("meety")

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """Eres un asistente de análisis de reuniones. Dado el transcript de una reunión,
genera un resumen estructurado en JSON con los siguientes campos:

{
  "executive_summary": "Resumen ejecutivo de 2-3 oraciones",
  "tasks": [
    {"description": "...", "assignee": "nombre o null", "due": "YYYY-MM-DD o null", "priority": "high|medium|low o null"}
  ],
  "commitments": [
    {"description": "...", "by": "nombre o null", "due": "YYYY-MM-DD o null"}
  ],
  "key_points": ["punto 1", "punto 2", ...],
  "next_meeting": "breve descripción o null"
}

Instrucciones:
- Extrae SOLO información explícitamente mencionada
- "assignee" y "by" solo si se nombra a alguien
- "due" solo si se menciona fecha
- Si no hay tareas, array vacío []
- Idioma del resumen: mismo que el del transcript
- JSON puro, sin markdown exterior"""


def _build_user_prompt(segments: list[TranscriptSegmentResponse], language: str | None) -> str:
    """Concatenate transcript segments into a single text block."""
    lines = []
    for seg in segments:
        speaker = seg.speaker or "Participante"
        text = seg.text.strip()
        lines.append(f"[{speaker}]: {text}")

    transcript_text = "\n".join(lines)
    lang_hint = f" (el transcript está en {language})" if language else ""
    return (
        f"Transcript de reunión{lang_hint}:\n\n{transcript_text}\n\n"
        "Genera el resumen JSON siguiendo el formato especificado."
    )


def _parse_raw_summary(raw_text: str | None) -> dict | None:
    """
    Try to extract a JSON object from the raw LLM output.
    Handles common formatting issues: leading/trailing whitespace, code fences.
    Returns None if extraction fails.
    """
    if not raw_text:
        return None
    text = raw_text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = text.lstrip("`")
        text = text[text.index("\n") + 1:] if "\n" in text else text
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try extracting first {...} block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


class Summarizer:
    """
    Client for OpenRouter chat completions API.
    Generates structured meeting summaries from transcript segments.
    """

    def __init__(self, *, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.model = model if model is not None else settings.OPENROUTER_MODEL
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=OPENROUTER_API_BASE,
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def summarize(
        self,
        segments: list[TranscriptSegmentResponse],
        *,
        meeting_id: int | None = None,
        language: str | None = None,
    ) -> MeetingSummary:
        """
        Generate a structured summary from transcript segments.

        Calls OpenRouter, parses the JSON response, and returns a MeetingSummary.
        Falls back to raw text on parse failure.
        """
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not configured — returning empty summary")
            return _empty_summary("OpenRouter API key not configured")

        user_prompt = _build_user_prompt(segments, language)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            raw_content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = _parse_raw_summary(raw_content)

            if parsed is None:
                logger.warning("Failed to parse LLM JSON — storing raw text")
                return _raw_text_summary(raw_content, self.model)

            # Validate and coerce into MeetingSummary shapes
            tasks = [
                TaskItem(
                    description=t.get("description", ""),
                    assignee=t.get("assignee"),
                    due=t.get("due"),
                    priority=t.get("priority"),
                )
                for t in parsed.get("tasks", [])
                if t.get("description")
            ]
            commitments = [
                CommitmentItem(
                    description=c.get("description", ""),
                    by=c.get("by"),
                    due=c.get("due"),
                )
                for c in parsed.get("commitments", [])
                if c.get("description")
            ]
            key_points = [
                p for p in parsed.get("key_points", []) if p
            ]

            return MeetingSummary(
                executive_summary=parsed.get("executive_summary", "") or "Sin resumen disponible.",
                tasks=tasks,
                commitments=commitments,
                key_points=key_points,
                next_meeting=parsed.get("next_meeting"),
                generated_at=datetime.now(timezone.utc),
                model=self.model,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter HTTP error: {e.response.status_code} — {e.response.text[:500]}")
            return _empty_summary(f"OpenRouter error: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return _empty_summary(f"Summarization failed: {e}")


def _empty_summary(reason: str) -> MeetingSummary:
    return MeetingSummary(
        executive_summary=f"[Resumen no disponible — {reason}]",
        tasks=[],
        commitments=[],
        key_points=[],
        next_meeting=None,
        generated_at=datetime.now(timezone.utc),
        model=None,
    )


def _raw_text_summary(raw: str, model: str | None) -> MeetingSummary:
    """Fallback when JSON parsing fails — return raw text as summary."""
    return MeetingSummary(
        executive_summary=(raw[:1000] if raw else "Sin contenido disponible."),
        tasks=[],
        commitments=[],
        key_points=[],
        next_meeting=None,
        generated_at=datetime.now(timezone.utc),
        model=model,
    )


# ── Convenience function ───────────────────────────────────────────────────────

async def generate_summary(
    segments: list[TranscriptSegmentResponse],
    *,
    meeting_id: int | None = None,
    language: str | None = None,
) -> MeetingSummary:
    """
    One-shot summary generation.
    Creates a Summarizer, calls it, and closes the client.
    """
    summarizer = Summarizer()
    try:
        return await summarizer.summarize(segments, meeting_id=meeting_id, language=language)
    finally:
        await summarizer.close()
