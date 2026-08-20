from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeatureConfig:
    """
    Configuration for Phase 2 feature engineering.
    """

    # Assume the project root is the parent of this Phase2 directory.
    project_root: Path = Path(__file__).resolve().parent.parent

    # Input from Phase 1
    phase1_bronze_path: Path = project_root / "Phase1" / "data" / "bronze" / "zomato_bronze.parquet"

    # Phase 2 specific data layout
    data_root: Path = project_root / "Phase2" / "data"
    silver_dir: Path = data_root / "silver"
    gold_dir: Path = data_root / "gold"

    # Filtering options
    target_city: str = "Bengaluru"
    min_rating: float = 0.0


FEATURE_CONFIG = FeatureConfig()

