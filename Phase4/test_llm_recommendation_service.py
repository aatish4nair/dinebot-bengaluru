"""
Tests for Phase 4 LLM recommendation service: get_enriched_recommendations (mocked).
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest

from Phase3.schemas import Recommendation, RestaurantRecord, UserPreferences
from Phase4.schemas import LLMEnrichedRecommendation


def test_get_enriched_recommendations_returns_empty_when_no_recs(monkeypatch):
    """When Phase 3 returns no recommendations, we return empty list."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_fake")
    with patch("Phase4.llm_recommendation_service.get_recommendations", return_value=[]):
        from Phase4.llm_recommendation_service import get_enriched_recommendations

        prefs = UserPreferences(place="UnknownLocality")
        out = get_enriched_recommendations(prefs)
        assert out == []


def test_get_enriched_recommendations_raises_when_no_api_key(monkeypatch):
    """When GROQ_API_KEY is not set, get_enriched_recommendations raises."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from Phase4.llm_recommendation_service import get_enriched_recommendations

    prefs = UserPreferences(place="Koramangala")
    # Ensure we have at least one recommendation so the code checks API key
    rec = Recommendation(
        restaurant=RestaurantRecord(
            name="X",
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=500,
            aggregate_rating=4.5,
            cuisines=["North Indian"],
        ),
        score=0.9,
    )
    with patch("Phase4.llm_recommendation_service.get_recommendations", return_value=[rec]):
        with pytest.raises((ValueError, Exception)) as exc_info:
            get_enriched_recommendations(prefs)
        assert "GROQ_API_KEY" in str(exc_info.value) or "API" in str(exc_info.value)


def test_get_enriched_recommendations_mocked_flow():
    """With Phase 3 and Groq mocked, we get back LLMEnrichedRecommendation list."""
    rec = Recommendation(
        restaurant=RestaurantRecord(
            name="Test Restaurant",
            city="Bengaluru",
            locality="Koramangala",
            average_cost_for_two=600,
            aggregate_rating=4.5,
            cuisines=["North Indian"],
        ),
        score=0.9,
    )
    mock_response = "Restaurant 1: Fits budget. Great rating and cuisine match."

    with patch("Phase4.llm_recommendation_service.get_recommendations", return_value=[rec]):
        with patch("Phase4.llm_recommendation_service.chat_completion", return_value=mock_response):
            from Phase4.llm_recommendation_service import get_enriched_recommendations

            prefs = UserPreferences(
                place="Koramangala",
                min_rating=4.0,
                max_price_for_two=1000,
                cuisines=["North Indian"],
            )
            out = get_enriched_recommendations(prefs, api_key="gsk_test")
            assert len(out) == 1
            assert isinstance(out[0], LLMEnrichedRecommendation)
            assert out[0].restaurant.name == "Test Restaurant"
            assert out[0].score == 0.9
            assert "Fits budget" in out[0].explanation or "budget" in out[0].explanation.lower()
