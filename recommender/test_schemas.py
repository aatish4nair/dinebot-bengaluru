from recommender.schemas import Recommendation, RestaurantRecord, UserPreferences


def test_user_preferences_defaults() -> None:
    prefs = UserPreferences()
    assert prefs.place is None
    assert prefs.min_rating is None
    assert prefs.max_price_for_two is None
    assert prefs.cuisines == []


def test_recommendation_holds_record_and_score() -> None:
    record = RestaurantRecord(
        name="Test Place",
        city="Bengaluru",
        locality="Koramangala",
        average_cost_for_two=500,
        aggregate_rating=4.5,
        cuisines=["North Indian"],
    )
    rec = Recommendation(restaurant=record, score=0.9)
    assert rec.restaurant.name == "Test Place"
    assert rec.score == 0.9



def _record(name, address=None, neighbourhood=None, locality="Indiranagar", source_url=None):
    return RestaurantRecord(
        name=name,
        city="Bengaluru",
        locality=locality,
        average_cost_for_two=500,
        aggregate_rating=4.0,
        cuisines=["North Indian"],
        address=address,
        neighbourhood=neighbourhood,
        source_url=source_url,
    )


def test_location_fields_default_to_none() -> None:
    record = _record("Test Place")
    assert record.address is None
    assert record.neighbourhood is None
    assert record.phone is None
    assert record.source_url is None


def test_same_name_different_address_are_different_outlets() -> None:
    a = _record("Cafe Coffee Day", "12th Main, Indiranagar, Bangalore")
    b = _record("Cafe Coffee Day", "4th Block, Jayanagar, Bangalore")
    assert a.outlet_id != b.outlet_id


def test_one_outlet_listed_under_several_categories_keeps_one_identity() -> None:
    """
    The source carries a separate URL per listing category, so the same
    premises appears as both a "Delivery" and a "Dine-out" row. Those must
    collapse to a single outlet, or one restaurant fills several cards.
    """
    delivery = _record("eat.fit", "1/8, 1st Stage, Indiranagar", source_url="https://z.com/a?ctx=delivery")
    dine_out = _record("eat.fit", "1/8, 1st Stage, Indiranagar", source_url="https://z.com/a?ctx=dineout")
    assert delivery.outlet_id == dine_out.outlet_id


def test_outlet_id_normalises_case_and_whitespace() -> None:
    assert _record("eat.fit", "1/8,  1st   Stage").outlet_id == _record("EAT.FIT", "1/8, 1st Stage").outlet_id


def test_outlet_id_falls_back_when_address_missing() -> None:
    a = _record("Chai Point", None, neighbourhood="Indiranagar")
    b = _record("Chai Point", None, neighbourhood="Jayanagar")
    assert a.outlet_id != b.outlet_id
    assert a.outlet_id  # still yields a usable key


def test_placeholder_address_does_not_merge_distinct_kitchens() -> None:
    """
    'Delivery Only' names no premises, so two delivery kitchens carrying it
    must still separate on their neighbourhood rather than collapsing.
    """
    south = _record("Supreme Biryani", "Delivery Only", neighbourhood="South Bangalore")
    east = _record("Supreme Biryani", "Delivery Only", neighbourhood="East Bangalore")
    assert south.outlet_id != east.outlet_id
    assert south.address == "Delivery Only"  # preserved verbatim on the record
