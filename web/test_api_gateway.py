"""
Tests for web API gateway: fetch_enriched_recommendations.
"""
import sys
from pathlib import Path
from unittest.mock import patch

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.schemas import UserPreferences
from web.api_gateway import fetch_enriched_recommendations


def _rec(name, address=None):
    from ai_explanations.schemas import LLMEnrichedRecommendation
    from recommender.schemas import RestaurantRecord

    return LLMEnrichedRecommendation(
        restaurant=RestaurantRecord(
            name=name,
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=500,
            aggregate_rating=4.0,
            cuisines=["North Indian"],
            address=address,
        ),
        score=0.9,
        explanation="Good match.",
    )


def _fetch(recs):
    with patch("web.api_gateway._ensure_groq_api_key", return_value="gsk_test"):
        with patch("web.api_gateway.get_enriched_recommendations") as mock_get:
            mock_get.return_value = recs
            prefs = UserPreferences(place="Koramangala")
            out = fetch_enriched_recommendations(prefs)
    return out


def test_fetch_enriched_recommendations_deduplicates_repeated_outlet():
    out = _fetch([_rec("A", "1 Main Rd"), _rec("A", "1 Main Rd"), _rec("B", "2 Main Rd")])
    assert len(out) == 2
    assert out[0].restaurant.name == "A"
    assert out[1].restaurant.name == "B"


def test_same_name_different_address_are_kept_as_separate_outlets():
    """Two branches of one chain are two destinations, not one."""
    out = _fetch([
        _rec("Cafe Coffee Day", "12th Main, Indiranagar, Bangalore"),
        _rec("Cafe Coffee Day", "4th Block, Jayanagar, Bangalore"),
    ])
    assert len(out) == 2
    assert {r.restaurant.address for r in out} == {
        "12th Main, Indiranagar, Bangalore",
        "4th Block, Jayanagar, Bangalore",
    }


def test_fetch_passes_api_key_through():
    with patch("web.api_gateway._ensure_groq_api_key", return_value="gsk_test"):
        with patch("web.api_gateway.get_enriched_recommendations") as mock_get:
            mock_get.return_value = [_rec("A", "1 Main Rd")]
            prefs = UserPreferences(place="Koramangala")
            fetch_enriched_recommendations(prefs)
    mock_get.assert_called_once_with(prefs, api_key="gsk_test")


def test_fetch_raises_when_no_api_key():
    import pytest
    with patch("web.api_gateway._ensure_groq_api_key", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            fetch_enriched_recommendations(UserPreferences(place="Koramangala"))
    assert "GROQ_API_KEY" in str(exc_info.value)
