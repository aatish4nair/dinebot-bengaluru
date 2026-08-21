from __future__ import annotations

from pathlib import Path

from datasets import Dataset

from . import config as phase2_config
from .filters import filter_by_min_rating, filter_city
from .feature_transformers import add_normalized_cuisines, add_price_and_rating_buckets
from .index_builder import build_locality_index, persist_feature_dataset


def _load_phase1_bronze(path: Path | None = None) -> Dataset:
    """
    Load the bronze dataset produced by data_ingestion.
    """
    parquet_path = path or phase2_config.FEATURE_CONFIG.bronze_input_path

    if not parquet_path.is_file():
        raise FileNotFoundError(
            f"data_ingestion bronze dataset not found at {parquet_path}. "
            "Run `python -m data_ingestion.ingestion_pipeline` first to generate it."
        )

    # Load the data_ingestion parquet using pandas, then wrap it as a Hugging Face
    # Dataset. This avoids split-related issues like
    # "Instruction 'train' corresponds to no data!" that come from using
    # the higher-level `load_dataset` APIs with a single-table parquet file.
    import pandas as pd
    from datasets import Dataset as HFDataset

    df = pd.read_parquet(parquet_path)
    return HFDataset.from_pandas(df, preserve_index=False)


def run_feature_engineering() -> tuple[Dataset, dict[str, list[int]], Path]:
    """
    Execute the full features feature engineering pipeline.

    Steps:
    1. Load data_ingestion bronze dataset.
    2. Filter to Bengaluru and by minimum rating.
    3. Add price/rating buckets and normalized cuisines.
    4. Persist the feature dataset (`silver`).
    5. Build a locality index and persist the same dataset as `gold`.

    Returns
    -------
    (dataset, locality_index, output_path)
    """
    bronze_ds = _load_phase1_bronze()

    filtered = filter_city(bronze_ds)
    filtered = filter_by_min_rating(filtered)

    featured = add_price_and_rating_buckets(filtered)
    featured = add_normalized_cuisines(featured)

    silver_path = phase2_config.FEATURE_CONFIG.silver_dir / "zomato_silver.parquet"
    persist_feature_dataset(featured, silver_path)

    # For now, gold is the same as silver; later phases may further optimize.
    gold_path = phase2_config.FEATURE_CONFIG.gold_dir / "zomato_gold.parquet"
    persist_feature_dataset(featured, gold_path)

    locality_index = build_locality_index(featured)

    return featured, locality_index, gold_path


if __name__ == "__main__":
    ds, index, path = run_feature_engineering()
    print(f"Feature engineering complete. Rows: {len(ds)}")
    print(f"Localities indexed: {len(index)}")
    print(f"Gold dataset written to: {path}")

