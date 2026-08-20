"""
Phase 5 – Streamlit entrypoint.

Run from project root: streamlit run Phase5/app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Load GROQ_API_KEY from the project root .env
_phase4_env = _root / ".env"


def _load_phase4_env() -> None:
    """Load the project root .env into os.environ so GROQ_API_KEY is available."""
    if not _phase4_env.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_phase4_env, override=False)
    except ImportError:
        pass
    if os.getenv("GROQ_API_KEY"):
        return
    try:
        for line in _phase4_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"").strip()
                if k == "GROQ_API_KEY" and v:
                    os.environ[k] = v
                    return
    except Exception:
        pass


_load_phase4_env()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

import streamlit as st

from Phase5.config import UI_CONFIG, TEXT_COLOR
from Phase5.state_management import (
    init_session_state,
    set_recommendations,
    set_error,
    set_loading,
)
from Phase5.components.filters_card import render_get_recommendation_card
from Phase5.components.results_view import render_top_recommendations
from Phase5.api_gateway import form_to_preferences, fetch_enriched_recommendations


st.set_page_config(
    page_title=UI_CONFIG.title,
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Background and global text color
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {UI_CONFIG.background_color};
    }}
    .main .block-container {{
        padding-top: 1.5rem;
        max-width: 900px;
    }}
    div[data-testid="stVerticalBlock"] {{
        color: {TEXT_COLOR};
    }}
    /* Get Recommendation card wrapper (matches ui.webp cream card) */
    .st-key-filters_card {{
        background-color: {UI_CONFIG.card_color};
        border-radius: 1.25rem;
        padding: 2rem 2.5rem 2.25rem 2.5rem;
        margin-bottom: 1.5rem;
    }}
    /* Button */
    .stButton > button {{
        background-color: {UI_CONFIG.button_bg_color} !important;
        color: {UI_CONFIG.button_text_color} !important;
        border-radius: 0.6rem !important;
        border: none !important;
        font-weight: 600;
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }}
    .stButton > button:focus:not(:active) {{
        box-shadow: none !important;
    }}
    /* Cap the selectbox dropdown's height so it always has enough room to
    open downward instead of flipping above the field (Streamlit picks
    whichever side has more space; capping the popup means it rarely needs
    more room than is available below, even in a shorter browser window). */
    div[data-testid="stSelectboxVirtualDropdown"] {{
        max-height: 160px !important;
    }}
    div[data-testid="stSelectboxVirtualDropdown"] ul {{
        max-height: 160px !important;
        overflow-y: auto !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

init_session_state(st)

# Header
st.markdown(
    f"""
    <div style="text-align: center; color: {UI_CONFIG.button_text_color}; margin-bottom: 0.5rem;">
        <h1 style="margin: 0;">{UI_CONFIG.title} 🍜 📍 🤖</h1>
        <p style="margin: 0.25rem 0 1rem 0; font-size: 1rem;">{UI_CONFIG.subtitle}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Get Recommendation: 4 dropdowns + button (no #f8eeeb wrapper bar)
(place, rating_label, price_label, cuisine), button_clicked = render_get_recommendation_card()

if button_clicked:
    set_loading(st, True)
    with st.spinner("Fetching recommendations..."):
        try:
            prefs = form_to_preferences(place, rating_label, price_label, cuisine)
            recs = fetch_enriched_recommendations(prefs)
            set_recommendations(st, recs)
        except Exception as e:
            set_error(st, str(e))
    set_loading(st, False)

if st.session_state.error_message:
    st.error(st.session_state.error_message)

if st.session_state.recommendations:
    render_top_recommendations(st.session_state.recommendations)
elif st.session_state.get("last_fetch_empty") and not st.session_state.get("error_message"):
    st.info("No recommendations found. Try relaxing filters (e.g. place, rating, price, or cuisine).")
