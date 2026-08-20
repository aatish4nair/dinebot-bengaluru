"""
Tests for Phase 5 API gateway: form_to_preferences and fetch_enriched_recommendations.
"""
import sys
from pathlib import Path
from unittest.mock import patch

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase3.schemas import UserPreferences
from Phase5.api_gateway import (
    form_to_preferences,
    fetch_enriched_recommendations,
    _rating_label_to_min_rating,
    _price_label_to_max_price,
)


def test_rating_label_to_min_rating():
    assert _rating_label_to_min_rating(None) is None
    assert _rating_label_to_min_rating("Choose a rating") is None
    assert _rating_label_to_min_rating("Less than 3.0") is None
    assert _rating_label_to_min_rating("3.0 - 4.0") == 3.0
    assert _rating_label_to_min_rating("4.0 - 5.0") == 4.0
    assert _rating_label_to_min_rating("More than 5.0") == 4.5


def test_price_label_to_max_price():
    assert _price_label_to_max_price(None) is None
    assert _price_label_to_max_price("Choose a price-range") is None
    assert _price_label_to_max_price("Less than ₹300") == 300.0
    assert _price_label_to_max_price("₹300 - ₹600") == 600.0
    assert _price_label_to_max_price("₹600 - ₹1000") == 1000.0
    assert _price_label_to_max_price("Above ₹1000") is None


def test_form_to_preferences_all_none():
    prefs = form_to_preferences(None, None, None, None)
    assert prefs.place is None
    assert prefs.min_rating is None
    assert prefs.max_price_for_two is None
    assert prefs.cuisines == []


def test_form_to_preferences_all_set():
    prefs = form_to_preferences(
        "Koramangala",
        "4.0 - 5.0",
        "₹600 - ₹1000",
        "North Indian",
    )
    assert prefs.place == "Koramangala"
    assert prefs.min_rating == 4.0
    assert prefs.max_price_for_two == 1000.0
    assert prefs.cuisines == ["North Indian"]


def test_form_to_preferences_placeholder_treated_as_none():
    from Phase5.config import PLACEHOLDER_PLACE, PLACEHOLDER_RATING, PLACEHOLDER_PRICE, PLACEHOLDER_CUISINE
    prefs = form_to_preferences(
        PLACEHOLDER_PLACE,
        PLACEHOLDER_RATING,
        PLACEHOLDER_PRICE,
        PLACEHOLDER_CUISINE,
    )
    assert prefs.place is None
    assert prefs.min_rating is None
    assert prefs.max_price_for_two is None
    assert prefs.cuisines == []


def test_fetch_enriched_recommendations_deduplicates_by_name():
    from Phase4.schemas import LLMEnrichedRecommendation
    from Phase3.schemas import RestaurantRecord

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
    with patch("Phase5.api_gateway._ensure_groq_api_key", return_value="gsk_test"):
        with patch("Phase5.api_gateway.get_enriched_recommendations") as mock_get:
            mock_get.return_value = [rec("A"), rec("A"), rec("B")]
            prefs = UserPreferences(place="Koramangala")
            out = fetch_enriched_recommendations(prefs)
    assert len(out) == 2
    assert out[0].restaurant.name == "A"
    assert out[1].restaurant.name == "B"
    mock_get.assert_called_once_with(prefs, api_key="gsk_test")


def test_fetch_raises_when_no_api_key():
    import pytest
    with patch("Phase5.api_gateway._ensure_groq_api_key", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            fetch_enriched_recommendations(UserPreferences(place="Koramangala"))
    assert "GROQ_API_KEY" in str(exc_info.value)
