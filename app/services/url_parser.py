"""
URL Parser para reuniones.

Extrae platform y native_meeting_id de URLs de Google Meet, Microsoft Teams y Zoom.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ParsedMeetingUrl(BaseModel):
    """Resultado del parsing de una URL de reunión."""

    platform: Literal["google_meet", "teams", "zoom"]
    native_meeting_id: str
    passcode: str | None = None
    original_url: str
    meeting_url: HttpUrl  # URL canónica reconstruida


class ParseError(ValueError):
    """URL de reunión no reconocida o malformada."""

    pass


# ——— Patterns ———

GOOGLE_MEET_RE = re.compile(
    r"https?://(?:meet\.google\.com/[\w-]+)"
)
TEAMS_RE = re.compile(
    r"https?://(?:teams\.live\.com/meet/\w+)"
)
ZOOM_RE = re.compile(
    r"https?://[\w.-]+/j/\d+"
)


def parse(url: str) -> ParsedMeetingUrl:
    """
    Parsea una URL de reunión y devuelve platform + native_meeting_id.

    Soporta:
    - Google Meet  → https://meet.google.com/abc-defg-hij
    - Microsoft Teams → https://teams.live.com/meet/1234567890123?p=XYZ
    - Zoom         → https://us05web.zoom.us/j/12345678901?pwd=...

    Raises:
        ParseError: si la URL no es reconocida como reunión válida.
    """
    url = url.strip()

    # — Google Meet —
    if "meet.google.com" in url:
        return _parse_google_meet(url)

    # — Microsoft Teams —
    if "teams.live.com" in url or "teams.microsoft.com" in url:
        return _parse_teams(url)

    # — Zoom —
    if "/j/" in url and "zoom.us" in url:
        return _parse_zoom(url)

    raise ParseError(
        f"URL no reconocida como reunión válida: {url!r}\n"
        "Esperado: Google Meet, Microsoft Teams o Zoom"
    )


def _parse_google_meet(url: str) -> ParsedMeetingUrl:
    """Extrae el ID de Google Meet."""
    match = re.search(r"meet\.google\.com/([\w-]+)", url)
    if not match:
        raise ParseError(f"Google Meet URL malformada: {url!r}")

    meeting_id = match.group(1)
    if len(meeting_id) < 5:
        raise ParseError(f"Google Meet ID inválido (muy corto): {meeting_id!r}")

    return ParsedMeetingUrl(
        platform="google_meet",
        native_meeting_id=meeting_id,
        passcode=None,
        original_url=url,
        meeting_url=f"https://meet.google.com/{meeting_id}",
    )


def _parse_teams(url: str) -> ParsedMeetingUrl:
    """Extrae el ID y passcode de Microsoft Teams."""
    import urllib.parse

    # Microsoft Teams — varios formatos de URL
    # Live:  https://teams.live.com/meet/1234567890123?p=XYZ
    # Web:   https://teams.microsoft.com/l/meetup-join/tenant/threadId?p=XYZ
    match = re.search(r"/(?:meetup-join|meet)/([^?&\s]+)", url)
    if not match:
        raise ParseError(f"Teams URL malformada: {url!r}")

    meeting_id = urllib.parse.unquote(match.group(1))
    passcode = None

    # Passcode en param 'p='
    p_match = re.search(r"[?&]p=([\w-]+)", url)
    if p_match:
        passcode = p_match.group(1)

    # Reconstruir URL canónica (solo numérico para live.com, con path para microsoft.com)
    if "teams.live.com" in url:
        canonical = f"https://teams.live.com/meet/{meeting_id}"
    else:
        canonical = f"https://teams.microsoft.com/l/meetup-join/{match.group(1)}"

    return ParsedMeetingUrl(
        platform="teams",
        native_meeting_id=meeting_id,
        passcode=passcode,
        original_url=url,
        meeting_url=canonical,  # type: ignore[arg]
    )


def _parse_zoom(url: str) -> ParsedMeetingUrl:
    """Extrae el ID numérico de Zoom y el passcode si está presente."""
    # Formato: https://us05web.zoom.us/j/12345678901?pwd=...
    match = re.search(r"/j/(\d+)", url)
    if not match:
        raise ParseError(f"Zoom URL malformada: {url!r}")

    meeting_id = match.group(1)
    passcode = None

    # Passcode puede venir en 'pwd=' o 'pk='
    pwd_match = re.search(r"[?&](?:pwd|pk)=([\w-]+)", url)
    if pwd_match:
        passcode = pwd_match.group(1)

    return ParsedMeetingUrl(
        platform="zoom",
        native_meeting_id=meeting_id,
        passcode=passcode,
        original_url=url,
        meeting_url=f"https://zoom.us/j/{meeting_id}",
    )
