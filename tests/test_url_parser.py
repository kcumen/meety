"""
Tests para url_parser.py
"""

import pytest
from app.services.url_parser import parse, ParseError, ParsedMeetingUrl


class TestGoogleMeet:
    """Google Meet URL parsing."""

    def test_basic_url(self):
        result = parse("https://meet.google.com/abc-defg-hij")
        assert result.platform == "google_meet"
        assert result.native_meeting_id == "abc-defg-hij"
        assert result.passcode is None
        assert str(result.meeting_url) == "https://meet.google.com/abc-defg-hij"

    def test_url_with_trailing_slash(self):
        result = parse("https://meet.google.com/abc-defg-hij/")
        assert result.platform == "google_meet"
        assert result.native_meeting_id == "abc-defg-hij"

    def test_url_strips_whitespace(self):
        result = parse("  https://meet.google.com/abc-defg-hij  ")
        assert result.native_meeting_id == "abc-defg-hij"

    def test_invalid_google_meet_url(self):
        with pytest.raises(ParseError):
            parse("https://meet.google.com/")
        with pytest.raises(ParseError):
            parse("https://meet.google.com/abc")  # too short


class TestMicrosoftTeams:
    """Microsoft Teams URL parsing."""

    def test_basic_url(self):
        result = parse("https://teams.live.com/meet/1234567890123")
        assert result.platform == "teams"
        assert result.native_meeting_id == "1234567890123"
        assert result.passcode is None

    def test_url_with_passcode(self):
        result = parse("https://teams.live.com/meet/1234567890123?p=XYZABC")
        assert result.platform == "teams"
        assert result.native_meeting_id == "1234567890123"
        assert result.passcode == "XYZABC"

    def test_teams_microsoft_com_url(self):
        result = parse("https://teams.microsoft.com/l/meetup-join/1234567890123")
        assert result.platform == "teams"
        assert result.native_meeting_id == "1234567890123"


class TestZoom:
    """Zoom URL parsing."""

    def test_basic_url(self):
        result = parse("https://us05web.zoom.us/j/12345678901")
        assert result.platform == "zoom"
        assert result.native_meeting_id == "12345678901"
        assert result.passcode is None

    def test_url_with_pwd(self):
        result = parse("https://us05web.zoom.us/j/12345678901?pwd=abcXYZ123")
        assert result.platform == "zoom"
        assert result.native_meeting_id == "12345678901"
        assert result.passcode == "abcXYZ123"

    def test_url_with_pk(self):
        result = parse("https://zoom.us/j/12345678901?pk=abcXYZ123")
        assert result.platform == "zoom"
        assert result.native_meeting_id == "12345678901"
        assert result.passcode == "abcXYZ123"


class TestParseError:
    """Error handling."""

    def test_invalid_url(self):
        with pytest.raises(ParseError):
            parse("https://google.com")

    def test_empty_string(self):
        with pytest.raises(ParseError):
            parse("")

    def test_whitespace_only(self):
        with pytest.raises(ParseError):
            parse("   ")

    def test_random_text(self):
        with pytest.raises(ParseError):
            parse("this is not a meeting url")
