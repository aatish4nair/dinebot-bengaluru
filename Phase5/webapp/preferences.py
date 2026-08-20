"""
Phase 5 (webapp) – Map the plain-HTML frontend's dropdown values to Phase 3's
UserPreferences.

This frontend uses its own option labels (`"3.0+"`, `"₹300 - ₹600"`, ...),
distinct from the older Streamlit UI's labels (`"3.0 - 4.0"`, `"Less than
₹300"`, ...) in Phase5/api_gateway.py. Kept separate so neither frontend's
tests/behaviour affect the other.
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase3.schemas import UserPreferences

# Rating options: "X+" means "X and above" - a direct min_rating threshold,
# unlike the older Streamlit UI's ambiguous bucket ranges.
RATING_OPTIONS = ["3.0+", "3.5+", "4.0+", "4.5+"]

# Price options: an upper bound on average cost for two. The lower edge of
# each bucket is informational only (not enforced), matching the original
# Phase 3 max_price_for_two semantics.
PRICE_OPTIONS = ["₹100 - ₹300", "₹300 - ₹600", "₹600 - ₹1000", "₹1000+"]

_PRICE_TO_MAX = {
    "₹100 - ₹300": 300.0,
    "₹300 - ₹600": 600.0,
    "₹600 - ₹1000": 1000.0,
    "₹1000+": None,
}


def rating_option_to_min_rating(value: str | None) -> float | None:
    """'3.5+' -> 3.5. Empty/unrecognized -> None (no minimum)."""
    if not value:
        return None
    text = value.strip()
    if text.endswith("+"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


def price_option_to_max_price(value: str | None) -> float | None:
    """'₹300 - ₹600' -> 600.0, '₹1000+' -> None (no maximum)."""
    if not value:
        return None
    return _PRICE_TO_MAX.get(value.strip())


def form_to_preferences(
    place: str | None,
    price: str | None,
    rating: str | None,
    cuisine: str | None,
) -> UserPreferences:
    """Convert the web form's raw values into a Phase 3 UserPreferences."""
    return UserPreferences(
        place=place.strip() if place else None,
        min_rating=rating_option_to_min_rating(rating),
        max_price_for_two=price_option_to_max_price(price),
        cuisines=[cuisine.strip()] if cuisine else [],
    )
