from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from datasets import Dataset

from . import config as recommendation_config
from .candidate_selector import row_to_restaurant_record, select_candidate_dataset
from .schemas import Recommendation, UserPreferences
from .scoring_engine import score_restaurant


@lru_cache(maxsize=8)
def _read_feature_dataset(parquet_path: Path) -> Dataset:
    """
    Read and parse the gold Parquet file at `parquet_path`, once per distinct
    path. The dataset doesn't change while the server is running, so this
    avoids re-reading and re-parsing the same file from disk on every
    request. Keyed by the resolved path (not "was a path passed in") so
    tests that point the config at a different, temporary file are
    unaffected and never see another test's/environment's cached data.
    """
    if not parquet_path.is_file():
        raise FileNotFoundError(f"features gold dataset not found at {parquet_path}")

    # Load the features gold parquet using pandas first, then wrap it in a
    # Hugging Face Dataset. This avoids internal split-related issues in
    # the `datasets` library that can manifest as
    # "Instruction 'train' corresponds to no data!" when using the higher
    # level parquet loading APIs.
    import pandas as pd
    from datasets import Dataset as HFDataset

    df = pd.read_parquet(parquet_path)
    return HFDataset.from_pandas(df, preserve_index=False)


def _within_price_range(price: float | None, preferences: UserPreferences) -> bool:
    """
    Whether `price` satisfies the user's selected range, both edges inclusive.

    A record with no recorded price fails a range the user actually selected -
    we cannot claim an unknown price falls inside it.
    """
    if preferences.min_price_for_two is None and preferences.max_price_for_two is None:
        return True
    try:
        value = float(price) if price is not None else None
    except (TypeError, ValueError):
        return False
    if value is None:
        return False
    if preferences.min_price_for_two is not None and value < float(preferences.min_price_for_two):
        return False
    if preferences.max_price_for_two is not None and value > float(preferences.max_price_for_two):
        return False
    return True


def _load_feature_dataset(path: Path | None = None) -> Dataset:
    """
    Load the feature-engineered dataset produced by features.
    """
    parquet_path = path or recommendation_config.RECOMMENDATION_CONFIG.gold_input_path
    return _read_feature_dataset(parquet_path)


def get_recommendations(preferences: UserPreferences) -> List[Recommendation]:
    """
    Public API for the recommendation engine.

    Loads the features feature dataset, filters candidates based on user preferences,
    scores them, and returns the top-K recommendations.

    Filtering is applied in this logical order:
        1. Place (locality within the default city)
        2. Rating (min_rating)
        3. Price range (min_price_for_two .. max_price_for_two, both inclusive)
        4. Cuisine

    Every one of those is a hard constraint. When nothing satisfies all four,
    the answer is an empty list - the caller shows an empty state rather than
    a page of restaurants the user did not ask for.
    """
    dataset = _load_feature_dataset()

    candidates_ds = select_candidate_dataset(dataset, preferences)

    recommendations: List[Recommendation] = []
    for row in candidates_ds:
        record = row_to_restaurant_record(row)
        # Safety: never include restaurants below user's min_rating (handles edge cases).
        if preferences.min_rating is not None:
            rating = record.aggregate_rating
            if rating is None or float(rating) < float(preferences.min_rating):
                continue
        # Safety: the selected price range is a hard constraint, so it is
        # re-checked here as well. Scoring runs below and sorting runs after
        # it; neither may promote a restaurant the user priced out.
        if not _within_price_range(record.average_cost_for_two, preferences):
            continue
        score = score_restaurant(record, preferences)
        recommendations.append(Recommendation(restaurant=record, score=score))

    # Always sort primarily by rating (descending), with score as a secondary
    # tie-breaker so that the highest-rated restaurants are returned first.
    def _sort_key(rec: Recommendation) -> tuple[float, float]:
        rating = rec.restaurant.aggregate_rating
        rating_value = float(rating) if rating is not None else 0.0
        return (rating_value, rec.score)

    recommendations.sort(key=_sort_key, reverse=True)
    top_k = recommendation_config.RECOMMENDATION_CONFIG.top_k
    return recommendations[:top_k]


if __name__ == "__main__":
    # Simple manual sanity check when running this module directly.
    sample_preferences = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1000,
        cuisines=["North Indian", "Chinese"],
    )
    recs = get_recommendations(sample_preferences)
    print(f"Found {len(recs)} recommendations.")
    for r in recs[:5]:
        print(f"- {r.restaurant.name} ({r.restaurant.locality}) -> score={r.score:.3f}")

