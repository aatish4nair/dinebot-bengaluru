from pathlib import Path

from datasets import Dataset

from data_ingestion.config import DATASET_CONFIG
from data_ingestion.dataset_downloader import download_dataset, persist_raw_dataset


def test_download_dataset_returns_dataset(tmp_path: Path) -> None:
    ds = download_dataset(cache_dir=tmp_path)
    assert isinstance(ds, Dataset)
    assert len(ds) > 0


def test_persist_raw_dataset_writes_parquet(tmp_path: Path) -> None:
    ds = download_dataset(cache_dir=tmp_path)

    dest_dir = tmp_path / "raw"
    path = persist_raw_dataset(ds, destination_dir=dest_dir)

    assert path.is_file()
    assert path.suffix == ".parquet"

