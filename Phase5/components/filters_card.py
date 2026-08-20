"""
Phase 5 – Get Recommendation card: 4 dropdowns and Get Recommendations button.

Place: 30 locations (alphabetical). Rating: 4 options. Price: 4 options. Cuisine: single select (alphabetical).
Placeholders are not included as selectable options (use empty/None and format_func).
"""
from __future__ import annotations

import streamlit as st

from Phase5.config import (
    UI_CONFIG,
    get_places,
    get_rating_options,
    get_price_options,
    get_cuisines,
    PLACEHOLDER_PLACE,
    PLACEHOLDER_RATING,
    PLACEHOLDER_PRICE,
    PLACEHOLDER_CUISINE,
    RATING_LABEL,
)


def render_get_recommendation_card() -> tuple:
    """
    Render the Get Recommendation card with 4 dropdowns and centered button.
    Returns (place, rating_label, price_label, cuisine) - placeholder values as None.
    """
    places = get_places()
    rating_opts = get_rating_options()
    price_opts = get_price_options()
    cuisines = get_cuisines()

    # Build options with empty first for placeholder (not a real option)
    place_options = [None] + places
    rating_options = [None] + rating_opts
    price_options = [None] + price_opts
    cuisine_options = [None] + cuisines

    def place_fmt(x):
        return x or PLACEHOLDER_PLACE

    def rating_fmt(x):
        return x or PLACEHOLDER_RATING

    def price_fmt(x):
        return x or PLACEHOLDER_PRICE

    def cuisine_fmt(x):
        return x or PLACEHOLDER_CUISINE

    with st.container(key="filters_card"):
        col1, col2 = st.columns(2)

        with col1:
            place = st.selectbox(
                "Place",
                options=place_options,
                format_func=place_fmt,
                key="place_select",
            )
            rating_label = st.selectbox(
                RATING_LABEL,
                options=rating_options,
                format_func=rating_fmt,
                key="rating_select",
            )

        with col2:
            price_label = st.selectbox(
                "Price Range",
                options=price_options,
                format_func=price_fmt,
                key="price_select",
            )
            cuisine = st.selectbox(
                "Cuisines",
                options=cuisine_options,
                format_func=cuisine_fmt,
                key="cuisine_select",
            )

        # Get Recommendations button, centered below the dropdowns
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            clicked = st.button(
                "Get Recommendations",
                type="primary",
                use_container_width=True,
                key="get_rec_btn",
            )

    return (place, rating_label, price_label, cuisine), clicked
