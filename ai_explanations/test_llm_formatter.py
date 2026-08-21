"""
Tests for ai_explanations LLM formatter: build_messages and parse_justifications.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.schemas import Recommendation, RestaurantRecord, UserPreferences

from ai_explanations.llm_formatter import build_messages, parse_justifications


def _make_rec(name: str, locality: str = "Koramangala") -> Recommendation:
    return Recommendation(
        restaurant=RestaurantRecord(
            name=name,
            city="Bengaluru",
            locality=locality,
            average_cost_for_two=500,
            aggregate_rating=4.2,
            cuisines=["North Indian"],
        ),
        score=0.9,
    )


def test_build_messages_structure():
    """Messages have system and user roles with expected content."""
    prefs = UserPreferences(place="Koramangala", min_rating=4.0)
    recs = [_make_rec("A"), _make_rec("B")]
    messages = build_messages(prefs, recs)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Koramangala" in messages[1]["content"]
    assert "A" in messages[1]["content"]
    assert "B" in messages[1]["content"]


def test_parse_justifications_empty_response():
    """Empty response yields fallback explanations."""
    recs = [_make_rec("A"), _make_rec("B")]
    out = parse_justifications("", recs)
    assert len(out) == 2
    assert "Good match" in out[0] or "Recommended" in out[0]
    assert "Good match" in out[1] or "Recommended" in out[1]


def test_parse_justifications_restaurant_format():
    """Lines like 'Restaurant 1: ...' are parsed by number."""
    recs = [_make_rec("A"), _make_rec("B")]
    response = """Restaurant 1: Fits your budget. Great rating.
Restaurant 2: Good value. Nice cuisines."""
    out = parse_justifications(response, recs)
    assert len(out) == 2
    assert "Fits your budget" in out[0] or "budget" in out[0].lower()
    assert "Good value" in out[1] or "cuisines" in out[1].lower()


def test_parse_justifications_numbered_format():
    """Lines like '1. ...' are parsed."""
    recs = [_make_rec("X")]
    response = "1. Affordable and highly rated. Matches your cuisine."
    out = parse_justifications(response, recs)
    assert len(out) == 1
    assert "Affordable" in out[0] or "rated" in out[0].lower() or "cuisine" in out[0].lower()


def test_parse_justifications_fallback_for_missing():
    """Missing numbers get fallback."""
    recs = [_make_rec("A"), _make_rec("B"), _make_rec("C")]
    response = """Restaurant 1: Only first.
Restaurant 3: Third."""
    out = parse_justifications(response, recs)
    assert len(out) == 3
    assert "Only first" in out[0] or "first" in out[0].lower()
    assert "Third" in out[2] or "third" in out[2].lower()
    assert "Good match" in out[1] or "Recommended" in out[1]
