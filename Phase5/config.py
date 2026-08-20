"""
Phase 5 – UI configuration, colors, and dropdown options.

Background: #71262b. Cards & button styling: #f8eeeb / #71262b. Text: #010203.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

# Theme (from ui.webp)
BACKGROUND_COLOR = "#71262b"
CARD_BACKGROUND_COLOR = "#f8eeeb"
BUTTON_BACKGROUND_COLOR = "#71262b"
BUTTON_TEXT_COLOR = "#f8eeeb"
TEXT_COLOR = "#010203"

# Placeholder texts – must NOT appear as dropdown options
PLACEHOLDER_PLACE = "Choose a place"
PLACEHOLDER_RATING = "Choose a rating"
PLACEHOLDER_PRICE = "Choose a price-range"
PLACEHOLDER_CUISINE = "Choose a cuisine"


@dataclass(frozen=True)
class UIConfig:
    """Configuration for Phase 5 Streamlit UI."""

    title: str = "DineBot Bengaluru"
    subtitle: str = "Choose your preferences and get your recommendations."
    max_recommendations: int = 10

    @property
    def background_color(self) -> str:
        return BACKGROUND_COLOR

    @property
    def card_color(self) -> str:
        return CARD_BACKGROUND_COLOR

    @property
    def text_color(self) -> str:
        return TEXT_COLOR

    @property
    def button_bg_color(self) -> str:
        return BUTTON_BACKGROUND_COLOR

    @property
    def button_text_color(self) -> str:
        return BUTTON_TEXT_COLOR


UI_CONFIG = UIConfig()


# Broad Bengaluru zone for each locality (display only, matches the
# "Location: <Zone> Bengaluru" line in ui.webp). Approximate real-world
# groupings; not used for filtering, only for the result card display.
LOCALITY_TO_REGION = {
    "MG Road": "Central",
    "Brigade Road": "Central",
    "Church Street": "Central",
    "Residency Road": "Central",
    "Lavelle Road": "Central",
    "Malleshwaram": "North",
    "Rajajinagar": "North",
    "New BEL Road": "North",
    "Frazer Town": "North",
    "Kalyan Nagar": "North",
    "Kammanahalli": "North",
    "Banashankari": "South",
    "Basavanagudi": "South",
    "Jayanagar": "South",
    "JP Nagar": "South",
    "BTM": "South",
    "Koramangala 4th Block": "South",
    "Koramangala 5th Block": "South",
    "Koramangala 6th Block": "South",
    "Koramangala 7th Block": "South",
    "HSR": "South",
    "Bannerghatta Road": "South",
    "Electronic City": "South",
    "Indiranagar": "East",
    "Old Airport Road": "East",
    "Marathahalli": "East",
    "Whitefield": "East",
    "Brookefield": "East",
    "Bellandur": "East",
    "Sarjapur Road": "East",
}


def get_region(locality: str | None) -> str:
    """Broad Bengaluru zone for a locality, for card display. Falls back to
    'Central' (the ui.webp default) for an unrecognized/missing locality."""
    return LOCALITY_TO_REGION.get((locality or "").strip(), "Central")


def get_places() -> List[str]:
    """
    30 Bengaluru locations in alphabetical order, matching the real values in
    the `listed_in(city)` column of the underlying Zomato dataset (via
    Phase1.schema_mapping, this becomes the `Locality` field). Placeholder
    not included. Keep in sync with the actual data so every option here can
    return results.
    """
    places = [
        "Banashankari",
        "Bannerghatta Road",
        "Basavanagudi",
        "Bellandur",
        "Brigade Road",
        "Brookefield",
        "BTM",
        "Church Street",
        "Electronic City",
        "Frazer Town",
        "HSR",
        "Indiranagar",
        "Jayanagar",
        "JP Nagar",
        "Kalyan Nagar",
        "Kammanahalli",
        "Koramangala 4th Block",
        "Koramangala 5th Block",
        "Koramangala 6th Block",
        "Koramangala 7th Block",
        "Lavelle Road",
        "Malleshwaram",
        "Marathahalli",
        "MG Road",
        "New BEL Road",
        "Old Airport Road",
        "Rajajinagar",
        "Residency Road",
        "Sarjapur Road",
        "Whitefield",
    ]
    return sorted(places)


RATING_LABEL = "Hotel Ratings"


def get_rating_options() -> List[str]:
    """4 rating options. Placeholder not included."""
    return [
        "Less than 3.0",
        "3.0 - 4.0",
        "4.0 - 5.0",
        "More than 5.0",
    ]


def get_price_options() -> List[str]:
    """4 price range options. Placeholder not included."""
    return [
        "Less than ₹300",
        "₹300 - ₹600",
        "₹600 - ₹1000",
        "Above ₹1000",
    ]


def get_cuisines() -> List[str]:
    """Cuisines in alphabetical order. Single-select; placeholder not included."""
    cuisines = [
        "Asian",
        "Bakery",
        "Biryani",
        "Cafe",
        "Chinese",
        "Continental",
        "Desserts",
        "Fast Food",
        "Healthy Food",
        "Indian",
        "Italian",
        "Japanese",
        "Mexican",
        "North Indian",
        "Pizza",
        "Seafood",
        "South Indian",
        "Street Food",
        "Thai",
    ]
    return sorted(cuisines)
