from __future__ import annotations

from typing import Iterable, List

from datasets import Dataset

from .config import RECOMMENDATION_CONFIG
from .schemas import RestaurantRecord, UserPreferences


def _normalize_text(value: str | None) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def _normalize_cuisine_list(cuisines: Iterable[str]) -> List[str]:
    return [c for c in (c.strip() for c in cuisines) if c]


def _row_matches_preferences(row: dict, preferences: UserPreferences) -> bool:
    # City constraint: treat "Bangalore" and "Bengaluru" as the same city.
    city_value = row.get("City")
    if isinstance(city_value, str):
        city_norm = _normalize_text(city_value)
        default_norm = _normalize_text(RECOMMENDATION_CONFIG.default_city)
        bengaluru_aliases = {"bangalore", "bengaluru"}
        if city_norm in bengaluru_aliases and default_norm in bengaluru_aliases:
            # Accept either spelling without filtering out the row.
            pass
        elif city_norm != default_norm:
            return False

    # Place / locality constraint – case-insensitive; match if either string contains the other.
    if preferences.place:
        locality_norm = _normalize_text(row.get("Locality"))
        place_norm = _normalize_text(preferences.place)
        if place_norm and place_norm not in locality_norm and locality_norm not in place_norm:
            return False

    # Min rating constraint.
    if preferences.min_rating is not None:
        rating = row.get("Aggregate rating")
        try:
            if rating is None or float(rating) < float(preferences.min_rating):
                return False
        except (TypeError, ValueError):
            return False

    # Max price constraint.
    if preferences.max_price_for_two is not None:
        price = row.get("Average Cost for two")
        try:
            if price is None or float(price) > float(preferences.max_price_for_two):
                return False
        except (TypeError, ValueError):
            return False

    # Cuisine overlap constraint (if user specified cuisines).
    if preferences.cuisines:
        target = {_normalize_text(c) for c in preferences.cuisines}
        normalized_cuisines = row.get("normalized_cuisines")

        if not isinstance(normalized_cuisines, list) or not normalized_cuisines:
            # Fallback to raw Cuisines string if normalized list is missing.
            raw = row.get("Cuisines") or ""
            normalized_cuisines = [part.strip() for part in str(raw).split(",")]

        available = {_normalize_text(c) for c in normalized_cuisines if c}
        if not (target & available):
            return False

    return True


def select_candidate_dataset(dataset: Dataset, preferences: UserPreferences) -> Dataset:
    """
    Filter the feature dataset to restaurants that satisfy the user preferences.
    """

    def _predicate(row: dict) -> bool:
        return _row_matches_preferences(row, preferences)

    return dataset.filter(_predicate)


def row_to_restaurant_record(row: dict) -> RestaurantRecord:
    """
    Convert a dataset row into a RestaurantRecord instance.
    """
    cuisines_list = row.get("normalized_cuisines")
    if not isinstance(cuisines_list, list):
        raw = row.get("Cuisines") or ""
        cuisines_list = [part.strip() for part in str(raw).split(",") if part.strip()]

    return RestaurantRecord(
        name=row.get("Restaurant Name", ""),
        city=row.get("City", ""),
        locality=row.get("Locality", ""),
        average_cost_for_two=row.get("Average Cost for two"),
        aggregate_rating=row.get("Aggregate rating"),
        cuisines=_normalize_cuisine_list(cuisines_list),
        price_bucket=row.get("price_bucket"),
        rating_bucket=row.get("rating_bucket"),
    )

