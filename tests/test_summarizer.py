"""
Tests for the summarizer service.
"""

import json

import pytest

from app.models import MeetingSummary, TranscriptSegmentResponse
from app.services.summarizer import (
    _build_user_prompt,
    _parse_raw_summary,
    _empty_summary,
    _raw_text_summary,
    Summarizer,
    generate_summary,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_SEGMENTS = [
    TranscriptSegmentResponse(
        start_time=0.0,
        end_time=10.5,
        text="Hola a todos, ¿cómo están?",
        speaker="Juan",
        language="es",
    ),
    TranscriptSegmentResponse(
        start_time=10.5,
        end_time=22.3,
        text="Muy bien Juan, gracias. Tenemos que hablar sobre el proyecto X.",
        speaker="María",
        language="es",
    ),
    TranscriptSegmentResponse(
        start_time=22.3,
        end_time=35.0,
        text="Sí, exactamente. Necesito que envíes el informe antes del viernes.",
        speaker="Juan",
        language="es",
    ),
]


VALID_JSON_RESPONSE = json.dumps({
    "executive_summary": "Reunión breve sobre el proyecto X. Juan se compromete a enviar el informe antes del viernes.",
    "tasks": [
        {"description": "Enviar informe del proyecto", "assignee": "Juan", "due": "2026-05-09", "priority": "high"}
    ],
    "commitments": [
        {"description": "Llamar al cliente el lunes", "by": "María", "due": "2026-05-11"}
    ],
    "key_points": ["Proyecto X necesita revisión", "Informe pendiente"],
    "next_meeting": "Próxima semana para seguimiento",
})


# ── _build_user_prompt ────────────────────────────────────────────────────────

class TestBuildUserPrompt:
    def test_basic(self):
        prompt = _build_user_prompt(SAMPLE_SEGMENTS, None)
        assert "[Juan]:" in prompt
        assert "[María]:" in prompt
        assert "Hola a todos" in prompt
        assert "envíes el informe" in prompt.lower()

    def test_with_language_hint(self):
        prompt = _build_user_prompt(SAMPLE_SEGMENTS, "es")
        assert "el transcript está en es" in prompt

    def test_empty_segments(self):
        prompt = _build_user_prompt([], None)
        assert "Transcript de reunión" in prompt
        assert "Genera el resumen" in prompt


# ── _parse_raw_summary ────────────────────────────────────────────────────────

class TestParseRawSummary:
    def test_plain_json(self):
        result = _parse_raw_summary(VALID_JSON_RESPONSE)
        assert result is not None
        assert "Reunión breve sobre el proyecto X" in result["executive_summary"]

    def test_markdown_code_fence(self):
        raw = "```json\n" + VALID_JSON_RESPONSE + "\n```"
        result = _parse_raw_summary(raw)
        assert result is not None
        assert "Reunión breve sobre el proyecto X" in result["executive_summary"]

    def test_markdown_code_fence_no_lang(self):
        raw = "```\n" + VALID_JSON_RESPONSE + "\n```"
        result = _parse_raw_summary(raw)
        assert result is not None
        assert "Reunión breve sobre el proyecto X" in result["executive_summary"]

    def test_json_surrounded_by_text(self):
        raw = 'Aquí está el resumen:\n{"executive_summary": "Test"}\nfin.'
        result = _parse_raw_summary(raw)
        assert result is not None
        assert result["executive_summary"] == "Test"

    def test_invalid_json_returns_none(self):
        result = _parse_raw_summary("Esto no es JSON {")
        assert result is None

    def test_none_input(self):
        result = _parse_raw_summary(None)
        assert result is None

    def test_empty_string(self):
        result = _parse_raw_summary("")
        assert result is None


# ── Summarizer.summarize ──────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestSummarizerSummarize:
    async def test_successful_summarize(self):
        import httpx
        import respx

        with respx.mock:
            respx.post(f"https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(200, json={
                    "choices": [{"message": {"content": VALID_JSON_RESPONSE}}],
                    "usage": {"total_tokens": 500},
                })
            )

            s = Summarizer(api_key="test-key", model="test/model")
            result = await s.summarize(SAMPLE_SEGMENTS, meeting_id=1, language="es")

            assert isinstance(result, MeetingSummary)
            assert "proyecto X" in result.executive_summary
            assert len(result.tasks) == 1
            assert result.tasks[0].assignee == "Juan"
            assert len(result.commitments) == 1
            assert len(result.key_points) == 2
            assert result.model == "test/model"
            await s.close()

    async def test_no_api_key_returns_empty(self):
        from app.services.summarizer import Summarizer

        # When api_key is empty, no HTTP call should be made
        s = Summarizer(api_key="")
        result = await s.summarize(SAMPLE_SEGMENTS)

        assert "no disponible" in result.executive_summary.lower()
        assert result.tasks == []
        await s.close()

    async def test_http_error_returns_empty(self):
        import httpx
        import respx

        with respx.mock:
            respx.post(f"https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(401, json={"error": "unauthorized"})
            )

            s = Summarizer(api_key="bad-key", model="test/model")
            result = await s.summarize(SAMPLE_SEGMENTS)

            assert "no disponible" in result.executive_summary.lower()
            await s.close()

    async def test_invalid_json_fallback(self):
        import httpx
        import respx

        with respx.mock:
            respx.post(f"https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(200, json={
                    "choices": [{"message": {"content": "Esto no es JSON válido {"}}],
                })
            )

            s = Summarizer(api_key="test-key", model="test/model")
            result = await s.summarize(SAMPLE_SEGMENTS)

            # Falls back to raw text
            assert result.executive_summary == "Esto no es JSON válido {"
            await s.close()

    async def test_empty_segments(self):
        import httpx
        import respx

        with respx.mock:
            respx.post(f"https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(200, json={
                    "choices": [{"message": {"content": VALID_JSON_RESPONSE}}],
                })
            )

            s = Summarizer(api_key="test-key")
            result = await s.summarize([])

            assert isinstance(result, MeetingSummary)
            await s.close()


# ── Convenience function ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestGenerateSummary:
    async def test_one_shot(self):
        import httpx
        import respx

        with respx.mock:
            respx.post(f"https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(200, json={
                    "choices": [{"message": {"content": VALID_JSON_RESPONSE}}],
                })
            )

            result = await generate_summary(SAMPLE_SEGMENTS, meeting_id=5, language="es")
            assert "proyecto X" in result.executive_summary
            assert len(result.tasks) == 1


# ── Fallback helpers ─────────────────────────────────────────────────────────

class TestFallbackHelpers:
    def test_empty_summary(self):
        result = _empty_summary("test reason")
        assert "test reason" in result.executive_summary
        assert result.tasks == []
        assert result.commitments == []
        assert result.generated_at is not None

    def test_raw_text_summary(self):
        result = _raw_text_summary("Raw LLM output here", "test/model")
        assert result.executive_summary == "Raw LLM output here"
        assert result.model == "test/model"
        assert result.tasks == []
