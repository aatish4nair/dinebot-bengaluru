from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import pyarrow.parquet as pq
from datasets import Dataset


def build_locality_index(dataset: Dataset) -> Dict[str, List[int]]:
    """
    Build an in-memory index mapping locality names to list of row indices.

    Some upstream datasets may not include a `Locality` column (for example if
    they renamed it or only expose a different locality field). In that case
    we simply return an empty index instead of raising, so later phases that
    don't rely on this index can still function.
    """

    # Try a few reasonable locality column names.
    candidate_columns = ["Locality", "locality", "locality_name"]
    locality_column = None
    for name in candidate_columns:
        if name in dataset.column_names:
            locality_column = name
            break

    if locality_column is None:
        # No locality-like column available; return an empty index gracefully.
        return {}

    index: Dict[str, List[int]] = defaultdict(list)
    for i, locality in enumerate(dataset[locality_column]):
        key = (locality or "").strip()
        if key:
            index[key].append(i)
    return dict(index)


def persist_feature_dataset(dataset: Dataset, output_path: Path) -> Path:
    """
    Persist feature-engineered dataset to Parquet.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(str(output_path))
    return output_path


def read_parquet_schema(path: Path) -> pq.ParquetFile:
    """
    Convenience helper used mainly in tests to inspect written Parquet files.
    """
    return pq.ParquetFile(str(path))

