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


def test_fetch_enriched_recommendations_deduplicates_by_name():
    from ai_explanations.schemas import LLMEnrichedRecommendation
    from recommender.schemas import RestaurantRecord

    rec = lambda name: LLMEnrichedRecommendation(
        restaurant=RestaurantRecord(
            name=name,
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=500,
            aggregate_rating=4.0,
            cuisines=["North Indian"],
        ),
        score=0.9,
        explanation="Good match.",
    )
    with patch("web.api_gateway._ensure_groq_api_key", return_value="gsk_test"):
        with patch("web.api_gateway.get_enriched_recommendations") as mock_get:
            mock_get.return_value = [rec("A"), rec("A"), rec("B")]
            prefs = UserPreferences(place="Koramangala")
            out = fetch_enriched_recommendations(prefs)
    assert len(out) == 2
    assert out[0].restaurant.name == "A"
    assert out[1].restaurant.name == "B"
    mock_get.assert_called_once_with(prefs, api_key="gsk_test")


def test_fetch_raises_when_no_api_key():
    import pytest
    with patch("web.api_gateway._ensure_groq_api_key", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            fetch_enriched_recommendations(UserPreferences(place="Koramangala"))
    assert "GROQ_API_KEY" in str(exc_info.value)
