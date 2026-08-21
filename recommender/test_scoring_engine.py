from recommender.schemas import RestaurantRecord, UserPreferences
from recommender.scoring_engine import score_restaurant


def test_higher_rating_gets_higher_score() -> None:
    prefs = UserPreferences(max_price_for_two=1000, cuisines=["North Indian"])

    low = RestaurantRecord(
        name="Low",
        city="Bengaluru",
        locality="Koramangala",
        average_cost_for_two=500,
        aggregate_rating=3.0,
        cuisines=["North Indian"],
    )
    high = RestaurantRecord(
        name="High",
        city="Bengaluru",
        locality="Koramangala",
        average_cost_for_two=500,
        aggregate_rating=4.5,
        cuisines=["North Indian"],
    )

    assert score_restaurant(high, prefs) > score_restaurant(low, prefs)


def test_price_penalty_applies_when_over_budget() -> None:
    prefs = UserPreferences(max_price_for_two=500)

    within = RestaurantRecord(
        name="Within",
        city="Bengaluru",
        locality="Koramangala",
        average_cost_for_two=400,
        aggregate_rating=4.0,
        cuisines=[],
    )
    over = RestaurantRecord(
        name="Over",
        city="Bengaluru",
        locality="Koramangala",
        average_cost_for_two=1000,
        aggregate_rating=4.0,
        cuisines=[],
    )

    assert score_restaurant(within, prefs) > score_restaurant(over, prefs)

