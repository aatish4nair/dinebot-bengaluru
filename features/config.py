from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeatureConfig:
    """
    Configuration for the feature engineering pipeline.
    """

    # Assume the project root is the parent of this features directory.
    project_root: Path = Path(__file__).resolve().parent.parent

    # Input from data_ingestion
    bronze_input_path: Path = project_root / "data_ingestion" / "data" / "bronze" / "zomato_bronze.parquet"

    # features specific data layout
    data_root: Path = project_root / "features" / "data"
    silver_dir: Path = data_root / "silver"
    gold_dir: Path = data_root / "gold"

    # Filtering options
    target_city: str = "Bengaluru"
    min_rating: float = 0.0


FEATURE_CONFIG = FeatureConfig()

