import asyncio
import pytest

from app.services.intent_detection import detect_intent, IntentCategory


@pytest.mark.parametrize(
    "message,expected",
    [
        ("I need a wedding RSVP page on June 12 at City Hall", IntentCategory.EVENT_INVITATION),
        ("Create a SaaS landing page for my analytics product", IntentCategory.LANDING_PAGE),
        ("Build a portfolio site for a freelance designer", IntentCategory.PORTFOLIO),
    ],
)
def test_detect_intent_categories(message, expected, monkeypatch):
    monkeypatch.setenv("ZAOYA_DISABLE_INTENT_AI", "1")
    result = asyncio.run(detect_intent(message))
    assert result.category == expected
    assert result.confidence > 0.4


def test_extract_event_fields(monkeypatch):
    monkeypatch.setenv("ZAOYA_DISABLE_INTENT_AI", "1")
    result = asyncio.run(detect_intent("Wedding invitation on June 12 at The Plaza, RSVP by May 30"))
    assert result.category == IntentCategory.EVENT_INVITATION
    assert result.inferred_fields.get("timing.date") == "June 12"
    assert result.inferred_fields.get("timing.location") == "The Plaza"
    assert result.inferred_fields.get("timing.rsvp_deadline") == "May 30"


def test_fallback_other(monkeypatch):
    monkeypatch.setenv("ZAOYA_DISABLE_INTENT_AI", "1")
    result = asyncio.run(detect_intent("Something totally different"))
    assert result.category == IntentCategory.OTHER
    assert result.confidence <= 0.4
