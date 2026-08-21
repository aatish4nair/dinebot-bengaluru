from pathlib import Path

from datasets import Dataset

from recommender import config as rec_config
from recommender.recommendation_service import get_recommendations
from recommender.schemas import UserPreferences


def test_get_recommendations_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """
    Integration-style test that runs the recommendation service against a small
    synthetic features gold dataset.
    """
    # 1. Create a tiny "gold" dataset.
    data = {
        "Restaurant Name": ["A", "B"],
        "City": ["Bengaluru", "Bengaluru"],
        "Locality": ["Koramangala", "Indiranagar"],
        "Aggregate rating": [4.5, 3.5],
        "Average Cost for two": [500, 1500],
        "Cuisines": ["North Indian, Chinese", "Italian"],
        "normalized_cuisines": [
            ["North Indian", "Chinese"],
            ["Italian"],
        ],
        "price_bucket": ["medium", "high"],
        "rating_bucket": ["high", "medium"],
    }
    ds = Dataset.from_dict(data)
    gold_dir = tmp_path / "features" / "data" / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    gold_path = gold_dir / "zomato_gold.parquet"
    ds.to_parquet(str(gold_path))

    # 2. Patch recommender config to reference this synthetic gold dataset.
    original = rec_config.RECOMMENDATION_CONFIG
    patched = type(original)(
        project_root=tmp_path,
        gold_input_path=gold_path,
        default_city=original.default_city,
        top_k=original.top_k,
        rating_weight=original.rating_weight,
        price_weight=original.price_weight,
        cuisine_weight=original.cuisine_weight,
    )
    monkeypatch.setattr(rec_config, "RECOMMENDATION_CONFIG", patched, raising=True)

    # 3. Call the recommendation API.
    prefs = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1000,
        cuisines=["North Indian"],
    )
    recs = get_recommendations(prefs)

    assert len(recs) == 1
    assert recs[0].restaurant.name == "A"
    assert recs[0].restaurant.locality == "Koramangala"

