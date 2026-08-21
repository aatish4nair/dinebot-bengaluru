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

