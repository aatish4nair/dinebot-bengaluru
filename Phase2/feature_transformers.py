from __future__ import annotations

from typing import Iterable, List

from datasets import Dataset


def _bucket_price(price_value: float | int | None) -> str | None:
    if price_value is None:
        return None
    try:
        value = float(price_value)
    except (TypeError, ValueError):
        return None

    if value < 500:
        return "low"
    if value < 1500:
        return "medium"
    return "high"


def _bucket_rating(rating_value: float | int | None) -> str | None:
    if rating_value is None:
        return None
    try:
        value = float(rating_value)
    except (TypeError, ValueError):
        return None

    if value < 3.0:
        return "low"
    if value < 4.0:
        return "medium"
    return "high"


def normalize_cuisines(cuisines_str: str | None) -> List[str]:
    """
    Convert a comma-separated cuisines string into a normalized list.
    """
    if not cuisines_str:
        return []
    parts = [p.strip() for p in cuisines_str.split(",")]
    return [p for p in parts if p]


def add_price_and_rating_buckets(dataset: Dataset) -> Dataset:
    """
    Add derived columns for price and rating buckets.
    """

    def _map_row(row: dict) -> dict:
        price = row.get("Average Cost for two")
        rating = row.get("Aggregate rating")
        row["price_bucket"] = _bucket_price(price)
        row["rating_bucket"] = _bucket_rating(rating)
        return row

    return dataset.map(_map_row)


def add_normalized_cuisines(dataset: Dataset) -> Dataset:
    """
    Add a list-valued `normalized_cuisines` column derived from `Cuisines`.
    """

    def _map_row(row: dict) -> dict:
        row["normalized_cuisines"] = normalize_cuisines(row.get("Cuisines"))
        return row

    return dataset.map(_map_row)

