from datasets import Dataset

from features.feature_transformers import (
    add_normalized_cuisines,
    add_price_and_rating_buckets,
    normalize_cuisines,
)


def test_normalize_cuisines_splits_and_strips() -> None:
    result = normalize_cuisines("North Indian, Chinese ,  South Indian ")
    assert result == ["North Indian", "Chinese", "South Indian"]


def test_add_price_and_rating_buckets_creates_expected_values() -> None:
    data = {
        "Average Cost for two": [300, 800, 2000],
        "Aggregate rating": [2.5, 3.5, 4.5],
    }
    ds = Dataset.from_dict(data)
    transformed = add_price_and_rating_buckets(ds)

    assert transformed["price_bucket"] == ["low", "medium", "high"]
    assert transformed["rating_bucket"] == ["low", "medium", "high"]


def test_add_normalized_cuisines_adds_list_column() -> None:
    data = {"Cuisines": ["North Indian, Chinese", None]}
    ds = Dataset.from_dict(data)
    transformed = add_normalized_cuisines(ds)

    assert transformed["normalized_cuisines"][0] == ["North Indian", "Chinese"]
    assert transformed["normalized_cuisines"][1] == []

