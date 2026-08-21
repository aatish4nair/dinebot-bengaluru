"""Tests for web.preferences: mapping the plain-HTML form to UserPreferences."""
from web.preferences import (
    form_to_preferences,
    price_option_to_max_price,
    rating_option_to_min_rating,
)


def test_rating_option_to_min_rating():
    assert rating_option_to_min_rating(None) is None
    assert rating_option_to_min_rating("") is None
    assert rating_option_to_min_rating("3.0+") == 3.0
    assert rating_option_to_min_rating("3.5+") == 3.5
    assert rating_option_to_min_rating("4.0+") == 4.0
    assert rating_option_to_min_rating("4.5+") == 4.5


def test_price_option_to_max_price():
    assert price_option_to_max_price(None) is None
    assert price_option_to_max_price("") is None
    assert price_option_to_max_price("₹100 - ₹300") == 300.0
    assert price_option_to_max_price("₹300 - ₹600") == 600.0
    assert price_option_to_max_price("₹600 - ₹1000") == 1000.0
    assert price_option_to_max_price("₹1000+") is None


def test_form_to_preferences_all_blank():
    prefs = form_to_preferences(None, None, None, None)
    assert prefs.place is None
    assert prefs.min_rating is None
    assert prefs.max_price_for_two is None
    assert prefs.cuisines == []


def test_form_to_preferences_all_set():
    prefs = form_to_preferences("Church Street", "₹300 - ₹600", "4.0+", "Continental")
    assert prefs.place == "Church Street"
    assert prefs.max_price_for_two == 600.0
    assert prefs.min_rating == 4.0
    assert prefs.cuisines == ["Continental"]


def test_form_to_preferences_empty_strings_treated_as_none():
    prefs = form_to_preferences("", "", "", "")
    assert prefs.place is None
    assert prefs.min_rating is None
    assert prefs.max_price_for_two is None
    assert prefs.cuisines == []
