"""
Phase 1 - Map the raw Hugging Face dataset schema to the canonical schema
used by Phase 2/3/4/5.

The `ManikaSaini/zomato-restaurant-recommendation` dataset (the classic
"Zomato Bangalore Restaurants" data) ships with lowercase, Bangalore-specific
column names:

    name, location, rate, votes, cuisines,
    approx_cost(for two people), listed_in(city), ...

Downstream phases (schema_validation.filter_invalid_rows, Phase 2 filters/
feature transformers, Phase 3 candidate_selector) all expect the canonical,
capitalized schema (`Restaurant Name`, `City`, `Locality`, `Cuisines`,
`Average Cost for two`, `Aggregate rating`). Without this mapping every row
is missing those fields and gets filtered out, producing an empty dataset.
"""
from __future__ import annotations

import re

from datasets import Dataset

# Every row in this dataset is a Bengaluru restaurant; there is no explicit
# city column, so we stamp a constant that matches Phase 2/3's target city.
DEFAULT_CITY = "Bengaluru"

_RATING_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _parse_rating(raw: object) -> float | None:
    """Parse values like '4.1/5', '3.5 /5', 'NEW', '-' into a float or None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"new", "-", "nan"}:
        return None
    match = _RATING_RE.match(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _parse_cost(raw: object) -> float | None:
    """Parse values like '1,200' or '800' into a float or None."""
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _map_row(row: dict) -> dict:
    return {
        "Restaurant Name": (row.get("name") or "").strip(),
        "City": DEFAULT_CITY,
        "Locality": (row.get("listed_in(city)") or row.get("location") or "").strip(),
        "Cuisines": (row.get("cuisines") or "").strip(),
        "Average Cost for two": _parse_cost(row.get("approx_cost(for two people)")),
        "Aggregate rating": _parse_rating(row.get("rate")),
        "Votes": row.get("votes"),
    }


def map_to_canonical_schema(dataset: Dataset) -> Dataset:
    """
    Transform the raw Hugging Face dataset into the canonical schema expected
    by Phase 2/3/4/5. Rows that already look canonical (e.g. in tests that
    build fixtures directly with the canonical column names) are returned
    unchanged.
    """
    if "Restaurant Name" in dataset.column_names:
        # Already canonical (e.g. synthetic test fixtures) - nothing to do.
        return dataset

    return dataset.map(_map_row, remove_columns=dataset.column_names)
