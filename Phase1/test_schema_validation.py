from datasets import Dataset

from Phase1.schema_validation import (
    EXPECTED_COLUMNS,
    ValidationResult,
    filter_invalid_rows,
    validate_schema,
)


def _build_small_dataset() -> Dataset:
    data = {
        "Restaurant Name": ["A", "B", None],
        "City": ["Bengaluru", "Bengaluru", "Bengaluru"],
        "Cuisines": ["North Indian", None, "Chinese"],
        "Aggregate rating": [4.5, 4.0, None],
    }
    # Add stub columns for the rest of EXPECTED_COLUMNS to avoid missing-column errors.
    for col in EXPECTED_COLUMNS:
        if col not in data:
            data[col] = [None, None, None]

    return Dataset.from_dict(data)


def test_validate_schema_detects_missing_and_extra_columns() -> None:
    ds = _build_small_dataset()
    # Remove a required column to simulate a mismatch.
    ds = ds.remove_columns("Votes")

    result = validate_schema(ds)
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "Votes" in result.missing_columns


def test_filter_invalid_rows_removes_rows_with_missing_critical_fields() -> None:
    ds = _build_small_dataset()
    filtered = filter_invalid_rows(ds)

    # Two rows have either missing name, cuisines, or rating.
    assert len(filtered) == 1
    assert filtered[0]["Restaurant Name"] == "A"

