from pathlib import Path

from datasets import Dataset

from features.index_builder import build_locality_index, persist_feature_dataset, read_parquet_schema


def test_build_locality_index_groups_by_locality() -> None:
    data = {
        "Locality": ["Koramangala", "Indiranagar", "Koramangala", ""],
    }
    ds = Dataset.from_dict(data)
    index = build_locality_index(ds)

    assert set(index.keys()) == {"Koramangala", "Indiranagar"}
    # Ensure indices are correct
    assert index["Koramangala"] == [0, 2]
    assert index["Indiranagar"] == [1]


def test_persist_feature_dataset_writes_parquet_and_schema(tmp_path: Path) -> None:
    data = {
        "A": [1, 2, 3],
    }
    ds = Dataset.from_dict(data)
    path = tmp_path / "out.parquet"

    written = persist_feature_dataset(ds, path)
    assert written.is_file()

    parquet_file = read_parquet_schema(written)
    assert parquet_file.schema is not None

