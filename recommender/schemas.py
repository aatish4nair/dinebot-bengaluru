from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class UserPreferences:
    """
    Preferences provided by the end user.
    """

    place: str | None = None  # e.g. locality in Bengaluru
    min_rating: float | None = None
    # A price *range* the user picked, e.g. "₹300 - ₹600". Both bounds are
    # inclusive and both are hard constraints: someone asking for ₹300-₹600
    # does not want a ₹150 result any more than a ₹900 one.
    min_price_for_two: float | None = None
    max_price_for_two: float | None = None
    cuisines: Sequence[str] = field(default_factory=list)


# Address values in the source that name no premises. They are real data, so
# they are preserved verbatim on the record, but they cannot separate one
# outlet from another: two different delivery kitchens both read "Delivery
# Only", so identity has to fall through to their neighbourhood instead.
_PLACEHOLDER_ADDRESSES = frozenset({"delivery only", "location varies", "takeaway only"})


# Words that mark an address as street-level rather than merely naming an area
# or a building. This is the same rule the location-coverage audit used to
# separate its ADDRESS_AVAILABLE records from its INSUFFICIENT_DATA ones, kept
# here so there is one definition of "specific enough" rather than two.
_STREET_LEVEL_TOKENS = re.compile(
    r"road|street|cross|main|layout|floor|block|stage|circle|market|"
    r"complex|mall|next to|opp|near|behind"
)


def has_street_level_detail(address: str | None) -> bool:
    """
    True when `address` pins a building rather than an area.

    A door number (any digit) or a street-level word is enough. Without either,
    the value names only a locality, complex or campus - "Prestige
    Shantiniketan, Whitefield, Bangalore" is a real place, but it is not the
    restaurant, and routing someone there drops them at a gate with no way to
    tell which unit they wanted.
    """
    text = (address or "").strip()
    if not text:
        return False
    return bool(re.search(r"\d", text) or _STREET_LEVEL_TOKENS.search(text.lower()))


def is_non_navigable_address(address: str | None) -> bool:
    """
    True when `address` names no premises a person could usefully travel to.

    Three cases, all treated the same by the UI - no Get Directions button:

    1. Missing, empty or whitespace-only.
    2. A placeholder: delivery-only and roaming kitchens have no premises.
       This includes rows where such an outlet appended detail to the
       placeholder ("Location Varies, 27th Main, HSR Layout, ..."), which is
       the one difference from the `_PLACEHOLDER_ADDRESSES` check used by
       `outlet_id`: identity deliberately treats those four rows as ordinary
       addresses so existing outlet ids stay stable, whereas navigation must
       reject them - "Location Varies" states outright that there is nowhere
       to go. Both rules read from the same placeholder set.
    3. Locality-only: a real address, but too coarse to represent the outlet.
    """
    text = (address or "").strip().lower()
    if not text:
        return True
    if text in _PLACEHOLDER_ADDRESSES or text.startswith("location varies"):
        return True
    return not has_street_level_detail(address)


@dataclass
class RestaurantRecord:
    """
    Minimal restaurant representation used by the recommendation engine.

    A record identifies one *physical outlet*, not a brand. `locality` is the
    Zomato listing zone the outlet is advertised under; `neighbourhood` and
    `address` describe where it actually is. All four location fields are
    optional because some source rows genuinely lack them - a missing address
    is preserved as None rather than filled in.
    """

    name: str
    city: str
    locality: str
    average_cost_for_two: float | None
    aggregate_rating: float | None
    cuisines: List[str]
    price_bucket: str | None = None
    rating_bucket: str | None = None
    address: str | None = None
    neighbourhood: str | None = None
    phone: str | None = None
    source_url: str | None = None

    @property
    def outlet_id(self) -> str:
        """
        Stable identity for this physical outlet: name + address.

        The name alone is NOT an identity - "Cafe Coffee Day" denotes 54
        different outlets in this dataset. The address is what separates them,
        so two records share an id only if they name the same premises.

        `source_url` is deliberately NOT used here. The source lists one URL
        per (outlet x listing category), so a single restaurant carries a
        different URL under "Delivery" than under "Dine-out" - 42,098 URLs
        across 9,660 real outlets. Keying on it would let the same outlet
        appear on several cards at once.

        Where no address was recorded, fall back to the outlet's neighbourhood
        and then its listing zone. That is weaker - two same-named outlets in
        one neighbourhood would still collide - but it never merges outlets
        that are known to sit at different addresses.
        """
        address = (self.address or "").strip()
        if address.lower() in _PLACEHOLDER_ADDRESSES:
            address = ""
        place = address or self.neighbourhood or self.locality or ""
        return " ".join(f"{self.name or ''}|{place}".lower().split())

    @property
    def navigation_ready(self) -> bool:
        """
        Whether this outlet has a physical address worth routing someone to.

        False for delivery-only and roaming kitchens and for records whose
        address never made it past a locality. The UI renders the Get
        Directions button only when this is True, so a card either offers a
        destination that exists or offers nothing at all.
        """
        return not is_non_navigable_address(self.address)


@dataclass
class Recommendation:
    """
    A ranked restaurant recommendation.
    """

    restaurant: RestaurantRecord
    score: float

