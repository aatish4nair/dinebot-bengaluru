"""
Tests for Phase 5 config: colors, 30 places, 4 rating/price options, cuisines.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase5.config import (
    BACKGROUND_COLOR,
    CARD_BACKGROUND_COLOR,
    TEXT_COLOR,
    PLACEHOLDER_PLACE,
    PLACEHOLDER_RATING,
    PLACEHOLDER_PRICE,
    PLACEHOLDER_CUISINE,
    get_places,
    get_rating_options,
    get_price_options,
    get_cuisines,
    UI_CONFIG,
)


def test_background_color():
    assert BACKGROUND_COLOR == "#71262b"


def test_card_color():
    assert CARD_BACKGROUND_COLOR == "#f8eeeb"


def test_text_color():
    assert TEXT_COLOR == "#010203"


def test_places_count_and_alphabetical():
    places = get_places()
    assert len(places) == 30
    assert places == sorted(places)
    assert PLACEHOLDER_PLACE not in places


def test_placeholder_not_in_places():
    assert "Choose a place" not in get_places()


def test_rating_options_four():
    opts = get_rating_options()
    assert len(opts) == 4
    assert "Less than 3.0" in opts
    assert "3.0 - 4.0" in opts
    assert "4.0 - 5.0" in opts
    assert "More than 5.0" in opts
    assert PLACEHOLDER_RATING not in opts


def test_price_options_four():
    opts = get_price_options()
    assert len(opts) == 4
    assert "Less than ₹300" in opts
    assert "₹300 - ₹600" in opts
    assert "₹600 - ₹1000" in opts
    assert "Above ₹1000" in opts
    assert PLACEHOLDER_PRICE not in opts


def test_cuisines_alphabetical_and_single_select():
    cuisines = get_cuisines()
    assert cuisines == sorted(cuisines)
    assert len(cuisines) >= 10
    assert PLACEHOLDER_CUISINE not in cuisines


def test_ui_config_properties():
    assert UI_CONFIG.background_color == "#71262b"
    assert UI_CONFIG.card_color == "#f8eeeb"
    assert UI_CONFIG.button_bg_color == "#71262b"
    assert UI_CONFIG.button_text_color == "#f8eeeb"
