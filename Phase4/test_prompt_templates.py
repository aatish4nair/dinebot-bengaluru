"""
Tests for Phase 4 prompt templates.
"""
import sys
from pathlib import Path

# Ensure project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase3.schemas import Recommendation, RestaurantRecord, UserPreferences

from Phase4.prompt_templates import (
    build_justification_prompt,
    build_restaurant_list,
    format_restaurant_for_prompt,
    format_user_preferences,
)


def test_format_user_preferences_empty():
    """No preferences yields a generic line."""
    prefs = UserPreferences()
    out = format_user_preferences(prefs)
    assert "preferences" in out.lower() or "general" in out.lower()


def test_format_user_preferences_full():
    """All fields present are formatted."""
    prefs = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1000,
        cuisines=["North Indian", "Chinese"],
    )
    out = format_user_preferences(prefs)
    assert "Koramangala" in out
    assert "4" in out
    assert "1000" in out
    assert "North Indian" in out
    assert "Chinese" in out


def test_format_restaurant_for_prompt():
    """Single restaurant line has name, locality, rating, cost, cuisines."""
    out = format_restaurant_for_prompt(
        1,
        "Test Restaurant",
        "Indiranagar",
        4.5,
        800,
        ["North Indian", "Chinese"],
    )
    assert "1." in out
    assert "Test Restaurant" in out
    assert "Indiranagar" in out
    assert "4.5" in out
    assert "800" in out
    assert "North Indian" in out


def test_build_restaurant_list_empty():
    """Empty list yields empty string."""
    out = build_restaurant_list([])
    assert out == ""


def test_build_restaurant_list_one():
    """One recommendation yields one numbered line."""
    rec = Recommendation(
        restaurant=RestaurantRecord(
            name="A",
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=500,
            aggregate_rating=4.2,
            cuisines=["North Indian"],
        ),
        score=0.9,
    )
    out = build_restaurant_list([rec])
    assert "1." in out
    assert "A" in out
    assert "Koramangala" in out


def test_build_justification_prompt():
    """Full prompt contains user prefs and restaurant list and instructions."""
    prefs = UserPreferences(place="Koramangala", min_rating=4.0)
    rec = Recommendation(
        restaurant=RestaurantRecord(
            name="B",
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=600,
            aggregate_rating=4.5,
            cuisines=["Chinese"],
        ),
        score=0.85,
    )
    out = build_justification_prompt(prefs, [rec])
    assert "Koramangala" in out
    assert "4" in out
    assert "B" in out
    assert "Restaurant 1" in out or "1." in out
    assert "two lines" in out.lower() or "2 lines" in out
