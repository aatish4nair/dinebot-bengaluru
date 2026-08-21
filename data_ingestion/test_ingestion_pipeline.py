from pathlib import Path

from datasets import Dataset

from data_ingestion.ingestion_pipeline import run_ingestion


def test_run_ingestion_produces_clean_dataset_and_file(tmp_path: Path, monkeypatch) -> None:
    """
    Integration-style test that runs the ingestion pipeline against the real dataset.

    The data directories are temporarily redirected to a tmp_path so the test
    does not affect the developer's filesystem.
    """
    from data_ingestion import config as config_module

    # Patch the DATASET_CONFIG paths to point at tmp_path.
    original_config = config_module.DATASET_CONFIG
    patched_config = type(original_config)(
        dataset_name=original_config.dataset_name,
        dataset_split=original_config.dataset_split,
        project_root=tmp_path,
        data_root=tmp_path / "data",
        raw_dir=tmp_path / "data" / "raw",
        bronze_dir=tmp_path / "data" / "bronze",
    )

    monkeypatch.setattr(config_module, "DATASET_CONFIG", patched_config, raising=True)

    cleaned_dataset, validation_result, output_path = run_ingestion()

    assert isinstance(cleaned_dataset, Dataset)
    assert len(cleaned_dataset) > 0
    assert output_path.is_file()

    # Schema should at least mostly match; we assert that no required column is missing.
    assert validation_result.is_valid

