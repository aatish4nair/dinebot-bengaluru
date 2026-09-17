"""
data_ingestion - Map the raw Hugging Face dataset schema to the canonical schema
used by features/3/4/5.

The `ManikaSaini/zomato-restaurant-recommendation` dataset (the classic
"Zomato Bangalore Restaurants" data) ships with lowercase, Bangalore-specific
column names:

    name, location, rate, votes, cuisines,
    approx_cost(for two people), listed_in(city), ...

Downstream phases (schema_validation.filter_invalid_rows, features filters/
feature transformers, recommender candidate_selector) all expect the canonical,
capitalized schema (`Restaurant Name`, `City`, `Locality`, `Cuisines`,
`Average Cost for two`, `Aggregate rating`). Without this mapping every row
is missing those fields and gets filtered out, producing an empty dataset.
"""
from __future__ import annotations

import re

from datasets import Dataset

# Every row in this dataset is a Bengaluru restaurant; there is no explicit
# city column, so we stamp a constant that matches features/3's target city.
DEFAULT_CITY = "Bengaluru"

_RATING_RE = re.compile(r"(\d+(?:\.\d+)?)")


# Characters that only appear when UTF-8 text was read as Latin-1 (often more
# than once). Used purely as a gate: a string without them is never touched.
_MOJIBAKE_MARKERS = re.compile(r"[ÃÂ]|â€")


def repair_mojibake(text: str, max_rounds: int = 12) -> str:
    """
    Undo UTF-8-decoded-as-Latin-1 corruption, e.g. 'CafÃ©' -> 'Café'.

    The source dump was re-encoded several times, so a value can carry the
    damage in layers ('CafÃƒÂ©' and worse); each round peels one layer off and
    we stop as soon as a round stops changing the string or the bytes no
    longer form valid UTF-8. Anything left in the CP1252 C1 range (curly
    quotes, dashes) is mapped back on the way out.

    This only ever repairs encoding damage - it does not normalize, translate
    or otherwise rewrite the value. Strings with no corruption markers are
    returned untouched, and any step that cannot round-trip cleanly leaves the
    value exactly as it was found.
    """
    if not text or not _MOJIBAKE_MARKERS.search(text):
        return text

    current = text
    for _ in range(max_rounds):
        try:
            candidate = current.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if candidate == current:
            break
        current = candidate

    if any("\x80" <= ch <= "\x9f" for ch in current):
        try:
            current = current.encode("latin-1").decode("cp1252")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    # Refuse a repair that left corruption behind or introduced control
    # characters - better to keep the original than to half-fix it.
    if _MOJIBAKE_MARKERS.search(current) or any(ch < " " for ch in current):
        return text
    return current


def _clean_optional(raw: object) -> str | None:
    """
    Strip a raw string field, returning None when it carries no usable value.

    Location fields are genuinely absent for some rows; we preserve that as
    None rather than an empty string so downstream code can tell "no address
    recorded" apart from "address is the empty string".
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    return repair_mojibake(text)


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
        "Restaurant Name": repair_mojibake((row.get("name") or "").strip()),
        "City": DEFAULT_CITY,
        "Locality": repair_mojibake((row.get("listed_in(city)") or row.get("location") or "").strip()),
        "Cuisines": repair_mojibake((row.get("cuisines") or "").strip()),
        "Average Cost for two": _parse_cost(row.get("approx_cost(for two people)")),
        "Aggregate rating": _parse_rating(row.get("rate")),
        "Votes": row.get("votes"),
        # Outlet-level location fields. `Locality` above comes from
        # `listed_in(city)`, which is the Zomato *listing zone* a restaurant is
        # advertised under - it disagrees with the outlet's real neighbourhood
        # in ~69% of rows. These four carry the physical outlet's own identity
        # through to the recommendation cards; without them a recommendation
        # names a brand ("Cafe Coffee Day") rather than a place you can go to.
        "Address": _clean_optional(row.get("address")),
        "Neighbourhood": _clean_optional(row.get("location")),
        "Phone": _clean_optional(row.get("phone")),
        "Source URL": _clean_optional(row.get("url")),
    }


def map_to_canonical_schema(dataset: Dataset) -> Dataset:
    """
    Transform the raw Hugging Face dataset into the canonical schema expected
    by features/3/4/5. Rows that already look canonical (e.g. in tests that
    build fixtures directly with the canonical column names) are returned
    unchanged.
    """
    if "Restaurant Name" in dataset.column_names:
        # Already canonical (e.g. synthetic test fixtures) - nothing to do.
        return dataset

    return dataset.map(_map_row, remove_columns=dataset.column_names)
