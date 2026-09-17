"""
web – Map the plain-HTML frontend's dropdown values to recommender's
UserPreferences.

Rating options are direct "X and above" thresholds (`"3.0+"`, `"3.5+"`, ...)
and price options are upper bounds on average cost for two (`"₹300 - ₹600"`,
...).
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.schemas import UserPreferences

# Rating options: "X+" means "X and above" - a direct min_rating threshold.
RATING_OPTIONS = ["3.0+", "3.5+", "4.0+", "4.5+"]

# Price options: an inclusive (min, max) range on average cost for two. Both
# edges are enforced - picking "₹300 - ₹600" must not return a ₹150
# restaurant. `None` as the upper edge means unbounded ("₹1000+").
PRICE_OPTIONS = ["₹100 - ₹300", "₹300 - ₹600", "₹600 - ₹1000", "₹1000+"]

_PRICE_TO_RANGE: dict[str, tuple[float | None, float | None]] = {
    "₹100 - ₹300": (100.0, 300.0),
    "₹300 - ₹600": (300.0, 600.0),
    "₹600 - ₹1000": (600.0, 1000.0),
    "₹1000+": (1000.0, None),
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


def price_option_to_range(value: str | None) -> tuple[float | None, float | None]:
    """'₹300 - ₹600' -> (300.0, 600.0). Empty/unrecognized -> (None, None)."""
    if not value:
        return (None, None)
    return _PRICE_TO_RANGE.get(value.strip(), (None, None))


def price_option_to_min_price(value: str | None) -> float | None:
    """'₹300 - ₹600' -> 300.0, '₹1000+' -> 1000.0."""
    return price_option_to_range(value)[0]


def price_option_to_max_price(value: str | None) -> float | None:
    """'₹300 - ₹600' -> 600.0, '₹1000+' -> None (no maximum)."""
    return price_option_to_range(value)[1]


def form_to_preferences(
    place: str | None,
    price: str | None,
    rating: str | None,
    cuisine: str | None,
) -> UserPreferences:
    """Convert the web form's raw values into a recommender UserPreferences."""
    min_price, max_price = price_option_to_range(price)
    return UserPreferences(
        place=place.strip() if place else None,
        min_rating=rating_option_to_min_rating(rating),
        min_price_for_two=min_price,
        max_price_for_two=max_price,
        cuisines=[cuisine.strip()] if cuisine else [],
    )
