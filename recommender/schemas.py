from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class UserPreferences:
    """
    Preferences provided by the end user.
    """

    place: str | None = None  # e.g. locality in Bengaluru
    min_rating: float | None = None
    max_price_for_two: float | None = None
    cuisines: Sequence[str] = field(default_factory=list)


@dataclass
class RestaurantRecord:
    """
    Minimal restaurant representation used by the recommendation engine.
    """

    name: str
    city: str
    locality: str
    average_cost_for_two: float | None
    aggregate_rating: float | None
    cuisines: List[str]
    price_bucket: str | None = None
    rating_bucket: str | None = None


@dataclass
class Recommendation:
    """
    A ranked restaurant recommendation.
    """

    restaurant: RestaurantRecord
    score: float

