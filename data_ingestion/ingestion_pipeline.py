from __future__ import annotations

from pathlib import Path

from datasets import Dataset

# Use absolute imports so this module works both as a script and as a package.
from data_ingestion.config import DATASET_CONFIG
from data_ingestion.dataset_downloader import download_dataset, persist_raw_dataset
from data_ingestion.schema_mapping import map_to_canonical_schema
from data_ingestion.schema_validation import ValidationResult, filter_invalid_rows, validate_schema


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_ingestion() -> tuple[Dataset, ValidationResult, Path]:
    """
    Run the complete data_ingestion ingestion pipeline.

    Steps:
    1. Download the dataset from Hugging Face into a local cache.
    2. Validate its schema.
    3. Filter obviously invalid rows.
    4. Persist the cleaned dataset to the bronze layer in Parquet format.

    Returns
    -------
    (dataset, validation_result, output_path)
    """
    raw_dataset = download_dataset()

    # Also persist a snapshot of the true raw dataset (original column names)
    # for reproducibility, before any renaming/mapping is applied.
    persist_raw_dataset(raw_dataset)

    # The Hugging Face dataset uses its own raw column names (name, rate,
    # approx_cost(for two people), listed_in(city), ...). Map it to the
    # canonical schema (Restaurant Name, City, Locality, Aggregate rating,
    # ...) that validation, filtering, and later phases all expect.
    canonical_dataset = map_to_canonical_schema(raw_dataset)

    validation_result = validate_schema(canonical_dataset)
    if not validation_result.is_valid:
        # We still proceed but signal to callers/tests that something is off.
        # Later phases can decide whether to be strict about this.
        pass

    cleaned_dataset = filter_invalid_rows(canonical_dataset)

    _ensure_directory(DATASET_CONFIG.bronze_dir)
    output_path = DATASET_CONFIG.bronze_dir / "zomato_bronze.parquet"
    cleaned_dataset.to_parquet(str(output_path))

    return cleaned_dataset, validation_result, output_path


if __name__ == "__main__":
    ds, result, path = run_ingestion()
    print(f"Ingestion complete. Valid schema: {result.is_valid}")
    if result.missing_columns:
        print(f"Missing columns: {result.missing_columns}")
    print(f"Bronze dataset written to: {path}")

