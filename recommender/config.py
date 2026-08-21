from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RecommendationConfig:
    """
    Configuration for the recommendation engine.
    """

    # Assume the project root is the parent of this recommender directory.
    project_root: Path = Path(__file__).resolve().parent.parent

    # Input from features
    gold_input_path: Path = project_root / "features" / "data" / "gold" / "zomato_gold.parquet"

    # Recommendation behaviour
    default_city: str = "Bengaluru"
    top_k: int = 10

    # Scoring weights
    rating_weight: float = 0.6
    price_weight: float = 0.2
    cuisine_weight: float = 0.2


RECOMMENDATION_CONFIG = RecommendationConfig()

