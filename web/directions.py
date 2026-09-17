"""
web - Build a Google Maps Directions link for a recommended outlet.

This module performs no network access and needs no credentials. It only
formats a public Google Maps URL from address data the recommendation already
carries; the sole Google interaction happens later, in the user's browser,
when they click the link.

The URL deliberately carries a destination and no `origin`. Google Maps then
uses whatever location the user has already granted *it* - DineBot never asks
for location permission, never reads GPS coordinates, and never learns where
the user is. DineBot knows where the restaurant is; Maps knows where the user
is; Maps does the routing, distance and ETA.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.schemas import RestaurantRecord, is_non_navigable_address

DIRECTIONS_BASE_URL = "https://www.google.com/maps/dir/?api=1&destination="

# Every outlet in this dataset is in Bengaluru; the state is never recorded per
# row, so it is appended as a constant to keep the query unambiguous.
STATE = "Karnataka"

# The source writes the city both ways - 96% of addresses already end in
# "Bangalore" - so appending "Bengaluru" to those would repeat the city under
# its other name. Matches the alias handling in recommender.candidate_selector.
_CITY_ALIASES = ({"bangalore", "bengaluru"},)


def _already_present(value: str, seen: str) -> bool:
    """True if `value` (or a known alias of it) is already in the text so far."""
    lowered = value.lower()
    if lowered in seen:
        return True
    for aliases in _CITY_ALIASES:
        if lowered in aliases and any(alias in seen for alias in aliases):
            return True
    return False


def build_destination(restaurant: RestaurantRecord) -> str | None:
    """
    Compose the destination text for `restaurant`, or None if it has none.

    The result is "<name>, <address>[, neighbourhood][, city][, state]".

    The name leads because it is what Maps matches a business listing on - an
    address alone often resolves to the building rather than the restaurant
    inside it. The address still does the real work of disambiguating: two
    outlets of one chain share a name, so name-only would route both to
    whichever branch Google guessed. Both come from *this* record, never from
    a lookup by name, so same-named outlets keep their own destinations.

    The neighbourhood, city and state are appended only when the address does
    not already name them, which keeps the query specific without repeating
    "Bangalore, Bangalore".

    Nothing here is invented - every part comes from the record, and a record
    with no usable address returns None rather than a guess.
    """
    if is_non_navigable_address(restaurant.address):
        return None

    address = (restaurant.address or "").strip()
    name = (restaurant.name or "").strip()
    parts = [name, address] if name else [address]
    seen = f"{name.lower()}, {address.lower()}" if name else address.lower()

    for extra in (restaurant.neighbourhood, restaurant.city, STATE):
        value = (extra or "").strip()
        if not value or _already_present(value, seen):
            continue
        parts.append(value)
        seen = f"{seen}, {value.lower()}"

    return ", ".join(parts)


def build_directions_url(restaurant: RestaurantRecord) -> str | None:
    """
    Return a Google Maps Directions URL for `restaurant`, or None.

    None means the caller must not render a Get Directions control at all -
    there is no destination to offer, and a dead or guessed link is worse than
    no link.
    """
    destination = build_destination(restaurant)
    if not destination:
        return None
    # `safe=""` so commas and slashes in Indian addresses are percent-encoded
    # rather than passed through as URL syntax.
    return f"{DIRECTIONS_BASE_URL}{quote(destination, safe='')}"
