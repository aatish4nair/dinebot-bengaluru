"""
Phase 5 – Adapter from UI form data to Phase 4 get_enriched_recommendations.

Maps dropdown values to UserPreferences, calls Phase 4, returns deduplicated list.
GROQ_API_KEY is loaded from the project root .env in app initialization; retrieve with os.getenv.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _ensure_groq_api_key() -> str | None:
    """Return GROQ_API_KEY from the environment if set."""
    return os.environ.get("GROQ_API_KEY")


from Phase3.schemas import UserPreferences
from Phase4.llm_recommendation_service import get_enriched_recommendations
from Phase4.schemas import LLMEnrichedRecommendation

from Phase5.config import (
    get_places,
    get_price_options,
    get_rating_options,
    PLACEHOLDER_PLACE,
    PLACEHOLDER_RATING,
    PLACEHOLDER_PRICE,
    PLACEHOLDER_CUISINE,
)


def _rating_label_to_min_rating(label: str | None) -> float | None:
    """Map rating dropdown label to Phase 3 min_rating."""
    if not label or label == PLACEHOLDER_RATING:
        return None
    if label == "Less than 3.0":
        return None  # no minimum
    if label == "3.0 - 4.0":
        return 3.0
    if label == "4.0 - 5.0":
        return 4.0
    if label == "More than 5.0":
        return 4.5  # top tier (ratings are 0–5)
    return None


def _price_label_to_max_price(label: str | None) -> float | None:
    """Map price range dropdown label to max_price_for_two."""
    if not label or label == PLACEHOLDER_PRICE:
        return None
    if label == "Less than ₹300":
        return 300.0
    if label == "₹300 - ₹600":
        return 600.0
    if label == "₹600 - ₹1000":
        return 1000.0
    if label == "Above ₹1000":
        return None  # no max
    return None


def form_to_preferences(
    place: str | None,
    rating_label: str | None,
    price_label: str | None,
    cuisine: str | None,
) -> UserPreferences:
    """Convert UI dropdown values to UserPreferences. Placeholder = None."""
    place_val = None if not place or place == PLACEHOLDER_PLACE else place
    rating_val = _rating_label_to_min_rating(rating_label)
    price_val = _price_label_to_max_price(price_label)
    cuisines_list = []
    if cuisine and cuisine != PLACEHOLDER_CUISINE:
        cuisines_list = [cuisine]
    return UserPreferences(
        place=place_val,
        min_rating=rating_val,
        max_price_for_two=price_val,
        cuisines=cuisines_list,
    )


def fetch_enriched_recommendations(preferences: UserPreferences) -> List[LLMEnrichedRecommendation]:
    """
    Call Phase 4 and return recommendations, deduplicated by restaurant name.
    Loads GROQ_API_KEY from the project root .env if not already in environment.
    """
    api_key = _ensure_groq_api_key()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to the project root .env (one line: GROQ_API_KEY=your_key)"
        )
    raw = get_enriched_recommendations(preferences, api_key=api_key)
    seen = set()
    out: List[LLMEnrichedRecommendation] = []
    for r in raw:
        name = (r.restaurant.name or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(r)
    return out
