"""
Tests for web config: places, cuisines, and locality-to-region lookup.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from web.config import get_cuisines, get_places, get_region


def test_places_count_and_alphabetical():
    places = get_places()
    assert len(places) == 30
    assert places == sorted(places)


def test_cuisines_alphabetical_and_single_select():
    cuisines = get_cuisines()
    assert cuisines == sorted(cuisines)
    assert len(cuisines) >= 10


def test_get_region_known_locality():
    assert get_region("Indiranagar") == "East"


def test_get_region_unknown_falls_back_to_central():
    assert get_region("Nowhere") == "Central"
    assert get_region(None) == "Central"
