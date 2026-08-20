from __future__ import annotations

from .config import RECOMMENDATION_CONFIG
from .schemas import RestaurantRecord, UserPreferences


def _safe_float(value: float | int | str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_restaurant(restaurant: RestaurantRecord, preferences: UserPreferences) -> float:
    """
    Compute a relevance score for a single restaurant.

    Heuristics:
    - Higher aggregate rating is better.
    - Prices under the user's max are slightly favoured; over the max are penalized.
    - Restaurants whose cuisines overlap more with the user's list are rewarded.
    """
    # Rating component
    rating_val = _safe_float(restaurant.aggregate_rating) or 0.0
    rating_component = (rating_val / 5.0) * RECOMMENDATION_CONFIG.rating_weight

    # Price component
    price_component = 0.0
    if preferences.max_price_for_two is not None:
        price_val = _safe_float(restaurant.average_cost_for_two)
        if price_val is not None:
            if price_val <= preferences.max_price_for_two:
                price_component = RECOMMENDATION_CONFIG.price_weight
            else:
                # Linear penalty as price exceeds the max.
                over_ratio = min((price_val - preferences.max_price_for_two) / max(preferences.max_price_for_two, 1.0), 1.0)
                price_component = RECOMMENDATION_CONFIG.price_weight * (1.0 - over_ratio)

    # Cuisine component
    cuisine_component = 0.0
    if preferences.cuisines:
        target = {c.lower().strip() for c in preferences.cuisines}
        have = {c.lower().strip() for c in restaurant.cuisines}
        if target:
            overlap = len(target & have)
            cuisine_component = RECOMMENDATION_CONFIG.cuisine_weight * (overlap / len(target))

    return rating_component + price_component + cuisine_component

