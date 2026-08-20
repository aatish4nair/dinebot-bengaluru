from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from datasets import Dataset


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of validating a dataset against an expected schema.
    """

    is_valid: bool
    missing_columns: Tuple[str, ...]
    extra_columns: Tuple[str, ...]


# The canonical schema produced by Phase1.schema_mapping.map_to_canonical_schema
# (not the raw Hugging Face dataset's own column names). This is what
# filter_invalid_rows and later phases (Phase 2/3) rely on.
EXPECTED_COLUMNS: Tuple[str, ...] = (
    "Restaurant Name",
    "City",
    "Locality",
    "Cuisines",
    "Average Cost for two",
    "Aggregate rating",
    "Votes",
)


def validate_schema(dataset: Dataset, required_columns: Iterable[str] = EXPECTED_COLUMNS) -> ValidationResult:
    """
    Validate that the dataset contains the expected columns.

    This is a lightweight structural validation step for Phase 1.
    """
    dataset_columns = set(dataset.column_names)
    required_set = set(required_columns)

    missing = tuple(sorted(required_set - dataset_columns))
    extra = tuple(sorted(dataset_columns - required_set))
    is_valid = not missing

    return ValidationResult(is_valid=is_valid, missing_columns=missing, extra_columns=extra)


def filter_invalid_rows(dataset: Dataset) -> Dataset:
    """
    Remove rows with critical missing values that would break later phases.
    """
    # Basic heuristic: ensure we have name, city, cuisines, and rating.
    return dataset.filter(
        lambda row: bool(row.get("Restaurant Name"))
        and bool(row.get("City"))
        and bool(row.get("Cuisines"))
        and row.get("Aggregate rating") is not None
    )

