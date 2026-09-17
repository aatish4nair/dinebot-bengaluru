"""
The selected price range is a hard constraint.

These tests pin the behaviour that was broken in production: picking
"₹300 - ₹600" returned ₹150 and ₹250 restaurants, because only the upper edge
of the range was ever enforced.
"""
from __future__ import annotations

import sys
from pathlib import Path

from datasets import Dataset

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.candidate_selector import select_candidate_dataset
from recommender.recommendation_service import get_recommendations
from recommender.schemas import UserPreferences
from web.preferences import PRICE_OPTIONS, form_to_preferences, price_option_to_range


def _dataset(rows):
    return Dataset.from_list([
        {
            "Restaurant Name": r.get("name", f"R{i}"),
            "City": "Bengaluru",
            "Locality": "Church Street",
            "Cuisines": "Indian",
            "normalized_cuisines": ["Indian"],
            "Average Cost for two": r["price"],
            "Aggregate rating": r.get("rating", 4.2),
            "Address": "12, Church Street, Bangalore",
            "Neighbourhood": "Church Street",
            "Phone": None,
            "Source URL": None,
            "price_bucket": None,
            "rating_bucket": None,
        }
        for i, r in enumerate(rows)
    ])


def _prices(dataset):
    return sorted(dataset["Average Cost for two"])


# --- the exact failing case -------------------------------------------------

def test_selected_range_excludes_cheaper_and_dearer_candidates():
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", "4.0+", "Indian")
    candidates = _dataset([{"price": p} for p in (150, 250, 300, 400, 600, 650)])
    assert _prices(select_candidate_dataset(candidates, prefs)) == [300, 400, 600]


# --- boundaries -------------------------------------------------------------

def test_boundaries_of_the_300_to_600_option():
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", None, None)
    candidates = _dataset([{"price": p} for p in (299, 300, 600, 601)])
    assert _prices(select_candidate_dataset(candidates, prefs)) == [300, 600]


def test_every_ui_price_option_enforces_both_edges():
    """Each option in PRICE_OPTIONS, at its own boundaries. No invented ranges."""
    for option in PRICE_OPTIONS:
        low, high = price_option_to_range(option)
        assert low is not None, option
        prefs = form_to_preferences("Church Street", option, None, None)

        below = _dataset([{"price": low - 1}])
        assert len(select_candidate_dataset(below, prefs)) == 0, f"{option}: {low - 1} should be excluded"

        at_low = _dataset([{"price": low}])
        assert len(select_candidate_dataset(at_low, prefs)) == 1, f"{option}: {low} should be included"

        if high is None:
            # "₹1000+" is unbounded above.
            assert len(select_candidate_dataset(_dataset([{"price": 99_999}]), prefs)) == 1, option
        else:
            assert len(select_candidate_dataset(_dataset([{"price": high}]), prefs)) == 1, \
                f"{option}: {high} should be included"
            assert len(select_candidate_dataset(_dataset([{"price": high + 1}]), prefs)) == 0, \
                f"{option}: {high + 1} should be excluded"


def test_price_option_range_mapping():
    assert price_option_to_range("₹100 - ₹300") == (100.0, 300.0)
    assert price_option_to_range("₹300 - ₹600") == (300.0, 600.0)
    assert price_option_to_range("₹600 - ₹1000") == (600.0, 1000.0)
    assert price_option_to_range("₹1000+") == (1000.0, None)
    assert price_option_to_range(None) == (None, None)
    assert price_option_to_range("nonsense") == (None, None)


def test_no_price_selected_means_no_price_constraint():
    prefs = form_to_preferences("Church Street", None, None, None)
    candidates = _dataset([{"price": p} for p in (50, 400, 9000)])
    assert _prices(select_candidate_dataset(candidates, prefs)) == [50, 400, 9000]


def test_unpriced_rows_are_excluded_when_a_range_is_selected():
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", None, None)
    candidates = _dataset([{"price": None}, {"price": 400}])
    assert _prices(select_candidate_dataset(candidates, prefs)) == [400]


# --- filtering happens before ranking / top-K -------------------------------

def test_ranking_advantages_cannot_reintroduce_an_out_of_range_restaurant(monkeypatch):
    """
    A cheap restaurant with a perfect rating and an exact cuisine match would
    outrank everything in range. It must still never appear.
    """
    dataset = _dataset([
        {"name": "Chikkanna Tiffin Room", "price": 150, "rating": 5.0},   # best rating, out of range
        {"name": "Siddiqu Kabab Center", "price": 250, "rating": 4.9},    # out of range
        {"name": "In Range A", "price": 400, "rating": 4.1},
        {"name": "In Range B", "price": 600, "rating": 4.0},
    ])
    monkeypatch.setattr("recommender.recommendation_service._load_feature_dataset", lambda *a, **k: dataset)

    prefs = form_to_preferences("Church Street", "₹300 - ₹600", "4.0+", "Indian")
    names = [r.restaurant.name for r in get_recommendations(prefs)]

    assert "Chikkanna Tiffin Room" not in names
    assert "Siddiqu Kabab Center" not in names
    assert names == ["In Range A", "In Range B"]


def test_unmatched_cuisine_returns_empty_rather_than_a_cheaper_alternative(monkeypatch):
    """
    This once covered the cuisine-relaxation fallback, which re-ran selection
    with no cuisine filter and had to keep the price range intact. Cuisine is
    now a hard constraint and that fallback is gone, so the same query returns
    nothing at all - and in particular never the ₹150 row.
    """
    dataset = _dataset([
        {"name": "Cheap Indian", "price": 150, "rating": 4.9},
        {"name": "In Range Indian", "price": 450, "rating": 4.1},
    ])
    monkeypatch.setattr("recommender.recommendation_service._load_feature_dataset", lambda *a, **k: dataset)

    # The fixtures are all "Indian"; "Japanese" matches nothing.
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", "4.0+", "Japanese")
    assert get_recommendations(prefs) == []

    # With a cuisine that does match, the price range is still enforced.
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", "4.0+", "Indian")
    recs = get_recommendations(prefs)
    assert [r.restaurant.name for r in recs] == ["In Range Indian"]
    assert all(300 <= r.restaurant.average_cost_for_two <= 600 for r in recs)


def test_every_returned_recommendation_is_inside_the_selected_range(monkeypatch):
    dataset = _dataset([{"name": f"R{p}", "price": p} for p in
                        (100, 150, 250, 299, 300, 400, 500, 600, 601, 800, 1200)])
    monkeypatch.setattr("recommender.recommendation_service._load_feature_dataset", lambda *a, **k: dataset)

    prefs = form_to_preferences("Church Street", "₹300 - ₹600", None, None)
    costs = [r.restaurant.average_cost_for_two for r in get_recommendations(prefs)]

    assert costs, "expected some recommendations"
    assert all(300 <= c <= 600 for c in costs), costs


def test_price_values_are_not_rewritten_to_fit_the_range(monkeypatch):
    """Excluded restaurants are dropped, never re-priced."""
    dataset = _dataset([{"name": "Cheap", "price": 250}, {"name": "Fits", "price": 400}])
    monkeypatch.setattr("recommender.recommendation_service._load_feature_dataset", lambda *a, **k: dataset)

    prefs = form_to_preferences("Church Street", "₹300 - ₹600", None, None)
    recs = get_recommendations(prefs)

    assert [r.restaurant.name for r in recs] == ["Fits"]
    assert recs[0].restaurant.average_cost_for_two == 400  # untouched
