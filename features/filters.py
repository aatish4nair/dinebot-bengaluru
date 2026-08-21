from __future__ import annotations

from datasets import Dataset

from .config import FEATURE_CONFIG


def filter_city(dataset: Dataset, city: str | None = None) -> Dataset:
    """
    Keep only rows whose City matches the target city (case-insensitive).
    """
    target = (city or FEATURE_CONFIG.target_city).lower()

    def _predicate(row: dict) -> bool:
        value = row.get("City")
        return isinstance(value, str) and value.lower() == target

    return dataset.filter(_predicate)


def filter_by_min_rating(dataset: Dataset, min_rating: float | None = None) -> Dataset:
    """
    Keep only rows whose Aggregate rating is >= min_rating.
    """
    threshold = FEATURE_CONFIG.min_rating if min_rating is None else float(min_rating)

    def _predicate(row: dict) -> bool:
        rating = row.get("Aggregate rating")
        if rating is None:
            return False
        try:
            return float(rating) >= threshold
        except (TypeError, ValueError):
            return False

    return dataset.filter(_predicate)

