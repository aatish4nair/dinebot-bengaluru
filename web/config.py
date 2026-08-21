"""
web – dropdown option lists and locality display data for the DineBot UI.
"""
from __future__ import annotations

from typing import List

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
    data_ingestion.schema_mapping, this becomes the `Locality` field). Keep in
    sync with the actual data so every option here can return results.
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


def get_cuisines() -> List[str]:
    """Cuisines in alphabetical order, single-select."""
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
