"""Tests for Phase5.webapp.server: the FastAPI app backing the HTML frontend."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from Phase3.schemas import RestaurantRecord
from Phase4.schemas import LLMEnrichedRecommendation
from Phase5.webapp.server import app

client = TestClient(app)


def _rec(name: str, locality: str = "Church Street") -> LLMEnrichedRecommendation:
    return LLMEnrichedRecommendation(
        restaurant=RestaurantRecord(
            name=name,
            city="Bengaluru",
            locality=locality,
            average_cost_for_two=500,
            aggregate_rating=4.2,
            cuisines=["Continental", "Cafe"],
        ),
        score=0.9,
        explanation=f"{name} is a great match.",
    )


def test_index_page_serves_html_with_real_options():
    response = client.get("/")
    assert response.status_code == 200
    assert "DineBot Bengaluru" in response.text
    # A real locality (from Phase5.config.get_places) should be present as an option.
    assert "Church Street" in response.text
    # A real cuisine should be present too.
    assert "Continental" in response.text


def test_recommendations_endpoint_returns_mapped_cards():
    with patch("Phase5.webapp.server.fetch_enriched_recommendations") as mock_fetch:
        mock_fetch.return_value = [_rec("Trick Or Treat"), _rec("Bangalore Masala House")]
        response = client.post(
            "/api/recommendations",
            json={"place": "Church Street", "price": "₹300 - ₹600", "rating": "3.0+", "cuisine": "Continental"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert len(body["recommendations"]) == 2
    first = body["recommendations"][0]
    assert first["rank"] == 1
    assert first["name"] == "Trick Or Treat"
    assert first["rating"] == 4.2
    assert first["cost"] == 500
    assert first["place"] == "Church Street"
    assert first["cuisines"] == ["Continental", "Cafe"]
    assert first["location"] == "Central Bengaluru"

    # Preferences were parsed correctly from the plain-HTML option values.
    prefs = mock_fetch.call_args[0][0]
    assert prefs.place == "Church Street"
    assert prefs.max_price_for_two == 600.0
    assert prefs.min_rating == 3.0
    assert prefs.cuisines == ["Continental"]


def test_recommendations_endpoint_empty_list_when_no_matches():
    with patch("Phase5.webapp.server.fetch_enriched_recommendations", return_value=[]):
        response = client.post("/api/recommendations", json={})
    assert response.status_code == 200
    assert response.json() == {"recommendations": [], "error": None}


def test_recommendations_endpoint_surfaces_missing_api_key_as_500():
    with patch("Phase5.webapp.server.fetch_enriched_recommendations", side_effect=ValueError("GROQ_API_KEY is not set")):
        response = client.post("/api/recommendations", json={})
    assert response.status_code == 500
    assert "GROQ_API_KEY" in response.json()["error"]


def test_recommendations_endpoint_surfaces_unexpected_errors_as_502():
    with patch("Phase5.webapp.server.fetch_enriched_recommendations", side_effect=RuntimeError("boom")):
        response = client.post("/api/recommendations", json={})
    assert response.status_code == 502
    assert "boom" in response.json()["error"]
