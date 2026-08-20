"""
Phase 5 – Top recommendations: card layout with numbered list and LLM explanation.
"""
from __future__ import annotations

from typing import List

import streamlit as st

from Phase5.config import UI_CONFIG, get_region

try:
    from Phase4.schemas import LLMEnrichedRecommendation
except ImportError:
    LLMEnrichedRecommendation = None  # type: ignore


def _star_rating(rating: float | None) -> str:
    """Render a 5-star string, e.g. 4.2 -> '★★★★☆' (rounded to nearest star)."""
    if rating is None:
        return "☆☆☆☆☆"
    filled = max(0, min(5, round(rating)))
    return "★" * filled + "☆" * (5 - filled)


def _card_css(card_color: str, text_color: str) -> str:
    return f"""
    .rec-card {{
        background-color: {card_color};
        color: {text_color};
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .rec-card h4 {{ color: {text_color}; margin-top: 0; }}
    .rec-card p {{ color: {text_color}; margin-bottom: 0.5rem; }}
    .rec-card .stars {{ color: #f0a500; letter-spacing: 0.1rem; }}
    .rec-card hr {{
        border: none;
        border-top: 1px solid rgba(1, 2, 3, 0.15);
        margin: 0.75rem 0;
    }}
    .rec-card .explanation {{ margin-bottom: 0; }}
    """


def render_top_recommendations(recommendations: List["LLMEnrichedRecommendation"]) -> None:
    """Render Top recommendations section: title bar + numbered cards (1., 2., ...)."""
    if not recommendations:
        return

    card_color = UI_CONFIG.card_color
    text_color = UI_CONFIG.text_color
    st.markdown(
        f"<style>{_card_css(card_color, text_color)}</style>",
        unsafe_allow_html=True,
    )

    # Section title with decorative divider (matches ui.webp)
    st.markdown(
        f"""
        <div style="text-align: center; margin: 0.5rem 0 1.5rem 0;">
            <h2 style="color: {UI_CONFIG.button_text_color}; margin: 0 0 0.4rem 0;">Top recommendations</h2>
            <div style="display: flex; align-items: center; justify-content: center; gap: 0.6rem;">
                <span style="flex: 0 1 120px; height: 1px; background-color: {UI_CONFIG.button_text_color}; opacity: 0.5;"></span>
                <span style="color: {UI_CONFIG.button_text_color}; opacity: 0.8;">&#9670;</span>
                <span style="flex: 0 1 120px; height: 1px; background-color: {UI_CONFIG.button_text_color}; opacity: 0.5;"></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def _render_card(rank: int, rec) -> None:
        r = rec.restaurant
        stars = _star_rating(r.aggregate_rating)
        rating_str = f"{r.aggregate_rating:.1f}" if r.aggregate_rating is not None else "N/A"
        cost_str = f"₹{r.average_cost_for_two:.0f}" if r.average_cost_for_two is not None else "N/A"
        cuisines_str = ", ".join(r.cuisines) if r.cuisines else "N/A"
        region = get_region(r.locality)
        st.markdown(
            f"""
            <div class="rec-card">
                <h4>{rank}. {r.name}</h4>
                <p><span class="stars">{stars}</span> &nbsp;<strong>Rating:</strong> {rating_str}</p>
                <p><strong>Place:</strong> {r.locality} &nbsp;|&nbsp; {cost_str}</p>
                <p><strong>Cuisines:</strong> {cuisines_str}</p>
                <p><strong>Location:</strong> {region} Bengaluru</p>
                <hr>
                <p class="explanation">{rec.explanation}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2-column grid (matches ui.webp side-by-side card layout)
    numbered = list(enumerate(recommendations, start=1))
    for row_start in range(0, len(numbered), 2):
        row = numbered[row_start : row_start + 2]
        cols = st.columns(2)
        for col, (rank, rec) in zip(cols, row):
            with col:
                _render_card(rank, rec)
