from pathlib import Path

from datasets import Dataset

from features.feature_pipeline import _load_phase1_bronze, run_feature_engineering
from features import config as phase2_config
from data_ingestion import config as phase1_config


def test__load_phase1_bronze_raises_if_missing(tmp_path: Path, monkeypatch) -> None:
    # Point features config at a non-existent file
    original_config = phase2_config.FEATURE_CONFIG
    patched = type(original_config)(
        project_root=tmp_path,
        bronze_input_path=tmp_path / "missing.parquet",
        data_root=tmp_path / "features" / "data",
        silver_dir=tmp_path / "features" / "data" / "silver",
        gold_dir=tmp_path / "features" / "data" / "gold",
        target_city=original_config.target_city,
        min_rating=original_config.min_rating,
    )
    monkeypatch.setattr(phase2_config, "FEATURE_CONFIG", patched, raising=True)

    try:
        _load_phase1_bronze()
        assert False, "Expected FileNotFoundError when bronze file is missing"
    except FileNotFoundError:
        pass


def test_run_feature_engineering_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """
    Integration-style test that runs the features pipeline end-to-end using a small synthetic
    dataset instead of the full Hugging Face dataset.
    """
    # 1. Patch data_ingestion config to write bronze data into tmp_path.
    original_phase1 = phase1_config.DATASET_CONFIG
    patched_phase1 = type(original_phase1)(
        dataset_name=original_phase1.dataset_name,
        dataset_split=original_phase1.dataset_split,
        project_root=tmp_path,
        data_root=tmp_path / "data_ingestion" / "data",
        raw_dir=tmp_path / "data_ingestion" / "data" / "raw",
        bronze_dir=tmp_path / "data_ingestion" / "data" / "bronze",
    )
    monkeypatch.setattr(phase1_config, "DATASET_CONFIG", patched_phase1, raising=True)

    # 2. Create a small synthetic "bronze" dataset and write it to the expected location.
    bronze_dir = patched_phase1.bronze_dir
    bronze_dir.mkdir(parents=True, exist_ok=True)
    bronze_path = bronze_dir / "zomato_bronze.parquet"
    data = {
        "City": ["Bengaluru", "Mumbai"],
        "Aggregate rating": [4.5, 4.0],
        "Average Cost for two": [500, 800],
        "Cuisines": ["North Indian, Chinese", "North Indian"],
        "Locality": ["Koramangala", "Andheri"],
    }
    ds = Dataset.from_dict(data)
    ds.to_parquet(str(bronze_path))

    # 3. Patch features config to use tmp_path as its project root.
    original_phase2 = phase2_config.FEATURE_CONFIG
    patched_phase2 = type(original_phase2)(
        project_root=tmp_path,
        bronze_input_path=bronze_path,
        data_root=tmp_path / "features" / "data",
        silver_dir=tmp_path / "features" / "data" / "silver",
        gold_dir=tmp_path / "features" / "data" / "gold",
        target_city=original_phase2.target_city,
        min_rating=original_phase2.min_rating,
    )
    monkeypatch.setattr(phase2_config, "FEATURE_CONFIG", patched_phase2, raising=True)

    # 4. Run features pipeline.
    dataset, locality_index, gold_path = run_feature_engineering()

    assert isinstance(dataset, Dataset)
    # Only Bengaluru row should remain.
    assert len(dataset) == 1
    assert dataset["City"][0] == "Bengaluru"
    assert "price_bucket" in dataset.column_names
    assert "rating_bucket" in dataset.column_names
    assert "normalized_cuisines" in dataset.column_names

    # Locality index should contain only Bengaluru's locality.
    assert list(locality_index.keys()) == ["Koramangala"]
    assert gold_path.is_file()

