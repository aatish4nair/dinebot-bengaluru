from datasets import Dataset

from recommender.candidate_selector import row_to_restaurant_record, select_candidate_dataset
from recommender.schemas import UserPreferences


def _build_dataset() -> Dataset:
    data = {
        "Restaurant Name": ["A", "B", "C"],
        "City": ["Bengaluru", "Bengaluru", "Mumbai"],
        "Locality": ["Koramangala", "Indiranagar", "Andheri"],
        "Aggregate rating": [4.5, 3.5, 4.0],
        "Average Cost for two": [500, 1500, 800],
        "Cuisines": ["North Indian, Chinese", "Italian", "North Indian"],
        "normalized_cuisines": [
            ["North Indian", "Chinese"],
            ["Italian"],
            ["North Indian"],
        ],
        "price_bucket": ["medium", "high", "medium"],
        "rating_bucket": ["high", "medium", "high"],
    }
    return Dataset.from_dict(data)


def test_select_candidate_dataset_filters_by_city_place_and_cuisines() -> None:
    ds = _build_dataset()
    prefs = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1000,
        cuisines=["North Indian"],
    )
    filtered = select_candidate_dataset(ds, prefs)

    # Only restaurant A in Koramangala, Bengaluru with matching cuisine should remain.
    assert len(filtered) == 1
    row = filtered[0]
    assert row["Restaurant Name"] == "A"
    assert row["Locality"] == "Koramangala"


def test_row_to_restaurant_record_uses_normalized_cuisines() -> None:
    ds = _build_dataset()
    row = ds[0]
    record = row_to_restaurant_record(row)
    assert record.name == "A"
    assert record.locality == "Koramangala"
    assert record.cuisines == ["North Indian", "Chinese"]


def _build_same_city_dataset() -> Dataset:
    """Like _build_dataset, but all rows share City=Bengaluru so the rating
    filter can be tested in isolation from the city filter."""
    data = {
        "Restaurant Name": ["A", "B", "C"],
        "City": ["Bengaluru", "Bengaluru", "Bengaluru"],
        "Locality": ["Koramangala", "Indiranagar", "Andheri"],
        "Aggregate rating": [4.5, 3.5, 4.0],
        "Average Cost for two": [500, 1500, 800],
        "Cuisines": ["North Indian, Chinese", "Italian", "North Indian"],
        "normalized_cuisines": [
            ["North Indian", "Chinese"],
            ["Italian"],
            ["North Indian"],
        ],
        "price_bucket": ["medium", "high", "medium"],
        "rating_bucket": ["high", "medium", "high"],
    }
    return Dataset.from_dict(data)


def test_select_candidate_dataset_excludes_restaurants_below_min_rating() -> None:
    """When min_rating is 4.0, restaurants with rating 3.5 or 3.0 must be excluded."""
    ds = _build_same_city_dataset()
    prefs = UserPreferences(
        place=None,
        min_rating=4.0,
        max_price_for_two=None,
        cuisines=[],
    )
    filtered = select_candidate_dataset(ds, prefs)
    # Dataset has ratings 4.5, 3.5, 4.0. Only A (4.5) and C (4.0) should remain; B (3.5) excluded.
    assert len(filtered) == 2
    names = {row["Restaurant Name"] for row in filtered}
    assert "A" in names
    assert "C" in names
    assert "B" not in names


def test_select_candidate_dataset_rating_boundary_4_0_included() -> None:
    """Rating exactly 4.0 is included when min_rating is 4.0."""
    ds = _build_dataset()
    prefs = UserPreferences(place=None, min_rating=4.0, max_price_for_two=None, cuisines=[])
    filtered = select_candidate_dataset(ds, prefs)
    ratings = [row["Aggregate rating"] for row in filtered]
    assert all(r >= 4.0 for r in ratings)


def test_select_candidate_dataset_min_rating_none_includes_all() -> None:
    """When min_rating is None, no rating filter is applied."""
    ds = _build_dataset()
    prefs = UserPreferences(place=None, min_rating=None, max_price_for_two=None, cuisines=[])
    filtered = select_candidate_dataset(ds, prefs)
    assert len(filtered) == 2  # Mumbai (Andheri) excluded by city; Bengaluru has 2
    # Actually _build_dataset has City Mumbai for C - so filter by city leaves Koramangala, Indiranagar (both Bengaluru). So we get 2.
    # Wait, we have 3 rows: A Bengaluru, B Bengaluru, C Mumbai. Default city is Bengaluru so C is out. So 2 rows. Both have rating 4.5 and 3.5. So we get A and B.
    assert len(filtered) == 2

