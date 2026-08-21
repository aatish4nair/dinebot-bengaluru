from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetConfig:
    """
    Configuration for data_ingestion data ingestion.
    """

    # Hugging Face dataset identifier
    dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    dataset_split: str = "train"

    # Local storage layout (relative to the project root)
    project_root: Path = Path(__file__).resolve().parent.parent
    data_root: Path = project_root / "data_ingestion" / "data"

    raw_dir: Path = data_root / "raw"
    bronze_dir: Path = data_root / "bronze"


DATASET_CONFIG = DatasetConfig()

