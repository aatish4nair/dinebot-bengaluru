"""
Tests for the Get Directions URL helper and the button's visibility rules.

The feature must stay a pure string builder: no Google API, no key, no
geolocation, and never an `origin` in the URL.
"""
import re
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.schemas import RestaurantRecord
from web.directions import build_destination, build_directions_url
from web.server import app

BASE = "https://www.google.com/maps/dir/?api=1&destination="


def _record(name="ABC Restaurant", address="123 MG Road, Bengaluru, Karnataka 560001",
            neighbourhood="MG Road", city="Bengaluru"):
    return RestaurantRecord(
        name=name, city=city, locality="MG Road",
        average_cost_for_two=500, aggregate_rating=4.2,
        cuisines=["South Indian"], address=address, neighbourhood=neighbourhood,
    )


# --- TEST 1: normal physical restaurant -------------------------------------

def test_normal_restaurant_is_navigation_ready_with_valid_url():
    r = _record()
    url = build_directions_url(r)
    assert r.navigation_ready is True
    assert url is not None
    assert url.startswith(BASE)
    assert "123%20MG%20Road" in url
    assert "origin=" not in url


# --- TEST 2: hotel ----------------------------------------------------------

def test_hotel_with_complete_address_is_navigation_ready():
    hotel = _record(name="Hotel Ramprasad",
                    address="22, Church Street, Ashok Nagar, Bengaluru",
                    neighbourhood="Church Street")
    assert hotel.navigation_ready is True
    url = build_directions_url(hotel)
    assert url.startswith(BASE)
    assert "Church%20Street" in url


# --- TESTS 3 & 4: delivery-only and location-varies --------------------------

def test_delivery_only_is_not_navigation_ready():
    r = _record(address="Delivery Only")
    assert r.navigation_ready is False
    assert build_directions_url(r) is None
    assert build_destination(r) is None


def test_location_varies_is_not_navigation_ready():
    for address in ("Location varies", "Location Varies, Bangalore",
                    "Location Varies, 27th Main, HSR Layout, HSR, Bangalore"):
        r = _record(address=address)
        assert r.navigation_ready is False, address
        assert build_directions_url(r) is None, address


def test_takeaway_only_is_not_navigation_ready():
    r = _record(address="Takeaway Only")
    assert r.navigation_ready is False
    assert build_directions_url(r) is None


# --- TESTS 5, 6, 7: missing / empty / whitespace addresses -------------------

def test_missing_empty_and_whitespace_addresses_are_not_navigation_ready():
    for address in (None, "", "   ", "\t\n "):
        r = _record(address=address)
        assert r.navigation_ready is False, repr(address)
        assert build_directions_url(r) is None, repr(address)


# --- TEST 8: special characters ---------------------------------------------

def test_special_characters_are_percent_encoded():
    r = _record(name="Andy's Café",
                address="Shop #4/B, Anvita's Kitchen, 1st Cross, Café Street",
                neighbourhood="Koramangala")
    url = build_directions_url(r)
    # Nothing raw that would break the query string.
    assert " " not in url
    assert "#" not in url
    assert url.count("?") == 1
    assert "%23" in url            # '#'
    assert "%2C" in url            # ','
    assert "%27" in url            # apostrophe
    assert "Caf%C3%A9" in url      # accented character, UTF-8 percent-encoded
    assert "origin=" not in url


# --- TEST 9: same-name outlets ----------------------------------------------

def test_same_name_outlets_produce_different_destinations():
    mg = _record(name="Cafe Coffee Day", address="MG Road, Bengaluru", neighbourhood="MG Road")
    brigade = _record(name="Cafe Coffee Day", address="Brigade Road, Bengaluru", neighbourhood="Brigade Road")

    mg_url, brigade_url = build_directions_url(mg), build_directions_url(brigade)
    assert mg_url != brigade_url
    assert "MG%20Road" in mg_url
    assert "Brigade%20Road" in brigade_url
    # Identity stays separate too, so both cards survive deduplication.
    assert mg.outlet_id != brigade.outlet_id


def test_destination_is_never_the_name_alone():
    r = _record(name="Cafe Coffee Day", address="MG Road, Bengaluru")
    destination = build_destination(r)
    assert destination != "Cafe Coffee Day"
    assert "MG Road" in destination


# --- TEST 10: origin is never specified -------------------------------------

def test_origin_never_appears_in_any_generated_url():
    records = [
        _record(),
        _record(name="Hotel Ramprasad", address="22, Church Street, Bengaluru"),
        _record(name="Andy's Café", address="Shop #4/B, 1st Cross"),
        _record(name="Cafe Coffee Day", address="Brigade Road, Bengaluru"),
    ]
    for r in records:
        url = build_directions_url(r)
        assert "origin=" not in url
        assert "origin" not in parse_qs(urlparse(url).query)


# --- TEST 11: no Google API dependency --------------------------------------

def test_implementation_has_no_google_api_or_geolocation_dependency():
    # Google-specific only: the project legitimately uses GROQ_API_KEY for the
    # LLM explanations, which has nothing to do with maps.
    banned = re.compile(
        r"GOOGLE_API_KEY|GOOGLE_MAPS_API_KEY|GOOGLE_PLACES_API_KEY|"
        r"maps\.googleapis\.com|places\.googleapis\.com|routes\.googleapis\.com|"
        r"navigator\.geolocation|googlemaps",
        re.IGNORECASE,
    )
    for path in ("web/directions.py", "web/server.py", "web/templates/index.html",
                 "recommender/schemas.py"):
        text = (_root / path).read_text(encoding="utf-8")
        found = banned.findall(text)
        assert not found, f"{path} references {found}"

    source = (_root / "web/directions.py").read_text(encoding="utf-8")
    for forbidden in ("requests", "httpx", "urlopen", "aiohttp"):
        assert forbidden not in source, f"directions.py must not perform network access ({forbidden})"


def test_only_google_reference_is_the_public_maps_url():
    source = (_root / "web/directions.py").read_text(encoding="utf-8")
    assert "https://www.google.com/maps/dir/?api=1&destination=" in source


# --- API contract -----------------------------------------------------------

def _payload_for(record):
    from ai_explanations.schemas import LLMEnrichedRecommendation
    enriched = [LLMEnrichedRecommendation(restaurant=record, score=0.9, explanation="Good match.")]
    with patch("web.server.fetch_enriched_recommendations", return_value=enriched):
        response = TestClient(app).post("/api/recommendations", json={"place": "MG Road"})
    assert response.status_code == 200
    return response.json()["recommendations"][0]


def test_api_exposes_navigation_ready_and_url_for_physical_outlet():
    card = _payload_for(_record())
    assert card["navigation_ready"] is True
    assert card["directions_url"].startswith(BASE)
    assert "origin=" not in card["directions_url"]


def test_api_withholds_directions_for_delivery_only_outlet():
    card = _payload_for(_record(address="Delivery Only"))
    assert card["navigation_ready"] is False
    assert card["directions_url"] is None


def test_existing_card_fields_are_unchanged():
    """The button must not disturb the fields the card already rendered."""
    card = _payload_for(_record())
    for key in ("rank", "name", "rating", "cost", "place", "cuisines", "location", "explanation"):
        assert key in card, key
    assert card["name"] == "ABC Restaurant"
    assert card["rating"] == 4.2


def test_city_is_not_repeated_under_its_other_name():
    """96% of addresses already end in 'Bangalore'; don't append 'Bengaluru' too."""
    r = _record(address="22, Church Street, Ashok Nagar, Bangalore", neighbourhood="Church Street")
    destination = build_destination(r)
    assert destination == "ABC Restaurant, 22, Church Street, Ashok Nagar, Bangalore, Karnataka"
    assert "Bengaluru" not in destination


def test_city_is_appended_when_address_omits_it():
    r = _record(address="22, Church Street, Ashok Nagar", neighbourhood="Church Street")
    assert build_destination(r) == "ABC Restaurant, 22, Church Street, Ashok Nagar, Bengaluru, Karnataka"


def test_neighbourhood_not_duplicated_when_already_in_address():
    r = _record(address="12, 4th Cross, Koramangala, Bangalore", neighbourhood="Koramangala")
    assert build_destination(r).count("Koramangala") == 1


# --- locality-only / insufficient addresses ---------------------------------

def test_locality_only_addresses_are_not_navigation_ready():
    """
    Real places, but they name an area or a complex rather than the outlet.
    Routing someone to a campus gate is worse than offering no button.
    """
    for address in (
        "Prestige Shantiniketan, Whitefield, Bangalore",
        "Babu Reddy Building, Electronic City, Bangalore",
        "Ferns City, Doddanekkundi, Whitefield, Bangalore",
        "Padmanabhanagar, Banashankari, Bangalore",
    ):
        r = _record(address=address)
        assert r.navigation_ready is False, address
        assert build_directions_url(r) is None, address


def test_door_number_makes_an_address_navigable():
    r = _record(address="54/A, Prestige Shantiniketan, Whitefield, Bangalore")
    assert r.navigation_ready is True
    assert build_directions_url(r).startswith(BASE)


def test_street_level_word_makes_an_address_navigable():
    """No digits, but a street-level word is enough to pin premises."""
    r = _record(address="Opp Forum Mall, Hosur Road, Koramangala, Bangalore")
    assert r.navigation_ready is True
    assert build_directions_url(r) is not None


def test_navigation_ready_matches_location_audit_classification():
    """
    navigation_ready must reuse the audit's location-quality rule, not a
    second taxonomy: delivery-only and INSUFFICIENT_DATA both hide the button.
    """
    from recommender.schemas import has_street_level_detail, is_non_navigable_address

    assert has_street_level_detail("3169-B, 12th Main, Indiranagar") is True
    assert has_street_level_detail("Prestige Shantiniketan, Whitefield") is False
    assert is_non_navigable_address("Delivery Only") is True
    assert is_non_navigable_address("Prestige Shantiniketan, Whitefield") is True
    assert is_non_navigable_address("3169-B, 12th Main, Indiranagar") is False


def test_api_withholds_directions_for_locality_only_outlet():
    card = _payload_for(_record(address="Prestige Shantiniketan, Whitefield, Bangalore"))
    assert card["navigation_ready"] is False
    assert card["directions_url"] is None


# --- destination must carry name AND address --------------------------------

def test_destination_contains_both_name_and_address():
    r = _record(name="Belgian Waffle Factory",
                address="22, Church Street, Ashok Nagar, Bangalore",
                neighbourhood="Church Street")
    destination = build_destination(r)
    assert destination.startswith("Belgian Waffle Factory, ")
    assert "22, Church Street, Ashok Nagar, Bangalore" in destination

    decoded = unquote(build_directions_url(r).split("destination=", 1)[1])
    assert "Belgian Waffle Factory" in decoded
    assert "22, Church Street, Ashok Nagar, Bangalore" in decoded


def test_hotel_destination_contains_both_name_and_address():
    r = _record(name="Hotel Tom's Restaurant",
                address="1/5, Muniswamy Garden, Richmond Road, Bangalore",
                neighbourhood="Richmond Road")
    decoded = unquote(build_directions_url(r).split("destination=", 1)[1])
    assert "Hotel Tom's Restaurant" in decoded
    assert "1/5, Muniswamy Garden, Richmond Road" in decoded


def test_same_name_outlets_keep_their_own_address_in_the_destination():
    mg = _record(name="Cakewala", address="12 MG Road, Bengaluru", neighbourhood="MG Road")
    brigade = _record(name="Cakewala", address="45 Brigade Road, Bengaluru", neighbourhood="Brigade Road")

    mg_dest, brigade_dest = build_destination(mg), build_destination(brigade)
    assert mg_dest.startswith("Cakewala, 12 MG Road")
    assert brigade_dest.startswith("Cakewala, 45 Brigade Road")
    assert build_directions_url(mg) != build_directions_url(brigade)


def test_ampersand_in_address_stays_encoded_with_name_prefix():
    r = _record(name="CakeZone", address="3 & 4, 6th Cross, 1st Main, BTM, Bangalore",
                neighbourhood="BTM")
    url = build_directions_url(r)
    assert "%26" in url                  # '&' escaped, does not split the query
    assert url.count("&") == 1           # only the api=1&destination separator
    assert "origin=" not in url
    assert unquote(url.split("destination=", 1)[1]).startswith("CakeZone, 3 & 4, 6th Cross")
