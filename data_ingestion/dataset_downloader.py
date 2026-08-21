from __future__ import annotations

from pathlib import Path
from typing import Optional

from datasets import Dataset, DatasetDict, load_dataset

from .config import DATASET_CONFIG


def _ensure_directory(path: Path) -> None:
    """
    Create a directory (and parents) if it does not already exist.
    """
    path.mkdir(parents=True, exist_ok=True)


def download_dataset(
    dataset_name: Optional[str] = None,
    split: Optional[str] = None,
    cache_dir: Optional[Path] = None,
) -> Dataset | DatasetDict:
    """
    Download the Zomato recommendation dataset from Hugging Face.

    Parameters
    ----------
    dataset_name:
        Optional override for the Hugging Face dataset identifier.
    split:
        Optional split to load. If omitted, the default from config is used.
    cache_dir:
        Optional directory where the dataset should be cached locally.

    Returns
    -------
    datasets.Dataset or datasets.DatasetDict
        The loaded dataset object.
    """
    name = dataset_name or DATASET_CONFIG.dataset_name
    dataset_split = split or DATASET_CONFIG.dataset_split

    # Use the raw_dir as a cache to keep data_ingestion self-contained.
    cache_directory = cache_dir or DATASET_CONFIG.raw_dir
    _ensure_directory(cache_directory)

    ds = load_dataset(name, split=dataset_split, cache_dir=str(cache_directory))
    return ds


def persist_raw_dataset(dataset: Dataset, destination_dir: Optional[Path] = None) -> Path:
    """
    Persist the raw dataset to disk in Parquet format for reproducibility.

    Returns
    -------
    Path
        The path to the written Parquet file.
    """
    dest_dir = destination_dir or DATASET_CONFIG.raw_dir
    _ensure_directory(dest_dir)

    parquet_path = dest_dir / "zomato_raw.parquet"
    dataset.to_parquet(str(parquet_path))
    return parquet_path

