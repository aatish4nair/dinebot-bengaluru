from datasets import Dataset

from Phase2.filters import filter_by_min_rating, filter_city


def _build_dataset() -> Dataset:
    data = {
        "City": ["Bengaluru", "bengaluru", "Mumbai"],
        "Aggregate rating": [4.5, 3.0, 4.0],
    }
    return Dataset.from_dict(data)


def test_filter_city_is_case_insensitive() -> None:
    ds = _build_dataset()
    filtered = filter_city(ds, city="Bengaluru")
    assert len(filtered) == 2
    assert all(city.lower() == "bengaluru" for city in filtered["City"])


def test_filter_by_min_rating_filters_below_threshold() -> None:
    ds = _build_dataset()
    filtered = filter_by_min_rating(ds, min_rating=4.0)
    assert len(filtered) == 2
    assert all(rating >= 4.0 for rating in filtered["Aggregate rating"])

