from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RecommendationConfig:
    """
    Configuration for Phase 3 recommendation engine.
    """

    # Assume the project root is the parent of this Phase3 directory.
    project_root: Path = Path(__file__).resolve().parent.parent

    # Input from Phase 2
    phase2_gold_path: Path = project_root / "Phase2" / "data" / "gold" / "zomato_gold.parquet"

    # Recommendation behaviour
    default_city: str = "Bengaluru"
    top_k: int = 10

    # Scoring weights
    rating_weight: float = 0.6
    price_weight: float = 0.2
    cuisine_weight: float = 0.2


RECOMMENDATION_CONFIG = RecommendationConfig()

