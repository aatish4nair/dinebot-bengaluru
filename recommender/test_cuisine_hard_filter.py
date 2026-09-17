"""
A selected cuisine is a hard constraint.

Regression for a production bug: selecting Lavelle Road / ₹600-₹1000 / 4.0+ /
Japanese returned six restaurants, none of them Japanese. `get_recommendations`
used to re-run candidate selection with `cuisines=[]` whenever the cuisine
filter matched nothing, backfilling the page with whatever else was in range.
"""
from __future__ import annotations

import sys
from pathlib import Path

from datasets import Dataset

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.recommendation_service import get_recommendations
from web.preferences import form_to_preferences, rating_option_to_min_rating


def _dataset(rows):
    return Dataset.from_list([
        {
            "Restaurant Name": r["name"],
            "City": "Bengaluru",
            "Locality": r.get("locality", "Lavelle Road"),
            "Cuisines": r["cuisines"],
            "normalized_cuisines": [c.strip() for c in r["cuisines"].split(",")],
            "Average Cost for two": r["price"],
            "Aggregate rating": r["rating"],
            "Address": "12, Lavelle Road, Bangalore",
            "Neighbourhood": "Lavelle Road",
            "Phone": None,
            "Source URL": None,
            "price_bucket": None,
            "rating_bucket": None,
        }
        for r in rows
    ])


def _use(monkeypatch, dataset):
    monkeypatch.setattr(
        "recommender.recommendation_service._load_feature_dataset",
        lambda *a, **k: dataset,
    )


def _has_cuisine(record, cuisine):
    return any(c.strip().lower() == cuisine.lower() for c in record.cuisines)


# --- the reported bug -------------------------------------------------------

def test_no_japanese_in_range_returns_empty_not_a_fallback_page(monkeypatch):
    """
    Lavelle Road / ₹600-₹1000 / 4.0+ / Japanese.

    The Japanese restaurants there are all above ₹1000; the highly-rated
    non-Japanese ones are in range. The engine must return nothing rather
    than the latter.
    """
    _use(monkeypatch, _dataset([
        # Japanese, but priced out.
        {"name": "Shiro", "cuisines": "Japanese, Asian", "price": 3000, "rating": 4.4},
        {"name": "Hammered", "cuisines": "Thai, Japanese", "price": 1300, "rating": 4.7},
        # Japanese and in range, but under-rated.
        {"name": "Swasthaa", "cuisines": "Italian, Japanese", "price": 600, "rating": 3.5},
        # In range and highly rated, but not Japanese - the old fallback page.
        {"name": "Truffles", "cuisines": "Cafe, American, Burger, Steak", "price": 900, "rating": 4.5},
        {"name": "Glen's Bakehouse", "cuisines": "Bakery, Cafe, Italian", "price": 600, "rating": 4.4},
        {"name": "The Konkan", "cuisines": "Seafood, Konkan", "price": 850, "rating": 4.4},
    ]))

    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹600 - ₹1000", "4.0+", "Japanese"))

    assert recs == [], [r.restaurant.name for r in recs]


def test_cuisine_is_never_silently_dropped_to_fill_the_page(monkeypatch):
    """Even with many in-range alternatives, none may substitute for the ask."""
    _use(monkeypatch, _dataset([
        {"name": f"Filler {i}", "cuisines": "Cafe, Desserts", "price": 700, "rating": 4.6}
        for i in range(20)
    ]))

    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹600 - ₹1000", "4.0+", "Japanese"))

    assert recs == []
    assert not any("Filler" in r.restaurant.name for r in recs)


# --- matching results are unaffected ----------------------------------------

def test_every_result_carries_the_selected_cuisine(monkeypatch):
    """Lavelle Road / ₹1000+ / 4.0+ / Japanese -> results exist, all Japanese."""
    _use(monkeypatch, _dataset([
        {"name": "Hammered", "cuisines": "Thai, Japanese, Cafe", "price": 1300, "rating": 4.7},
        {"name": "MISU", "cuisines": "Asian, Japanese, Korean", "price": 1700, "rating": 4.5},
        {"name": "Shiro", "cuisines": "Japanese, Asian", "price": 3000, "rating": 4.4},
        {"name": "Truffles", "cuisines": "Cafe, American", "price": 2000, "rating": 4.9},
    ]))

    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹1000+", "4.0+", "Japanese"))

    assert recs, "expected Japanese results above ₹1000"
    assert all(_has_cuisine(r.restaurant, "Japanese") for r in recs), \
        [(r.restaurant.name, r.restaurant.cuisines) for r in recs]
    assert "Truffles" not in [r.restaurant.name for r in recs]


def test_existing_matching_behaviour_is_unchanged(monkeypatch):
    """Indiranagar / ₹600-₹1000 / 4.0+ / North Indian keeps working."""
    _use(monkeypatch, _dataset([
        {"name": "Hotel Tom's Restaurant", "locality": "Indiranagar",
         "cuisines": "Mangalorean, Seafood, Chinese, North Indian", "price": 1000, "rating": 4.4},
        {"name": "Tandoori Taal", "locality": "Indiranagar",
         "cuisines": "Biryani, North Indian", "price": 900, "rating": 4.3},
        {"name": "Not Indian", "locality": "Indiranagar",
         "cuisines": "Cafe, Desserts", "price": 800, "rating": 4.8},
    ]))

    recs = get_recommendations(form_to_preferences("Indiranagar", "₹600 - ₹1000", "4.0+", "North Indian"))

    names = [r.restaurant.name for r in recs]
    assert names == ["Hotel Tom's Restaurant", "Tandoori Taal"]
    assert all(_has_cuisine(r.restaurant, "North Indian") for r in recs)


# --- matching semantics -----------------------------------------------------

def test_cuisine_match_is_case_and_whitespace_insensitive(monkeypatch):
    _use(monkeypatch, _dataset([
        {"name": "Odd Casing", "cuisines": "  japanese ,  Asian ", "price": 700, "rating": 4.2},
    ]))
    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹600 - ₹1000", "4.0+", "Japanese"))
    assert [r.restaurant.name for r in recs] == ["Odd Casing"]


def test_cuisine_match_is_not_fuzzy(monkeypatch):
    """A different cuisine that merely contains the word must not match."""
    _use(monkeypatch, _dataset([
        {"name": "Japanese Curry House", "cuisines": "Japanese Curry", "price": 700, "rating": 4.2},
        {"name": "Not Japanese", "cuisines": "Chinese, Thai", "price": 700, "rating": 4.3},
    ]))
    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹600 - ₹1000", "4.0+", "Japanese"))
    assert recs == [], [r.restaurant.name for r in recs]


# --- rating semantics unchanged ---------------------------------------------

def test_rating_option_semantics_are_greater_or_equal():
    assert rating_option_to_min_rating("3.5+") == 3.5
    assert rating_option_to_min_rating("4.0+") == 4.0
    assert rating_option_to_min_rating("4.5+") == 4.5


def test_rating_threshold_is_inclusive(monkeypatch):
    _use(monkeypatch, _dataset([
        {"name": "Exactly 4.0", "cuisines": "Japanese", "price": 700, "rating": 4.0},
        {"name": "Just Under", "cuisines": "Japanese", "price": 700, "rating": 3.9},
    ]))
    recs = get_recommendations(form_to_preferences("Lavelle Road", "₹600 - ₹1000", "4.0+", "Japanese"))
    assert [r.restaurant.name for r in recs] == ["Exactly 4.0"]
