"""
Phase 5 – Streamlit session state for inputs and results.
"""
from __future__ import annotations

from typing import Any, List

# Type alias for enriched recommendations (Phase 4 output)
try:
    from Phase4.schemas import LLMEnrichedRecommendation
except ImportError:
    LLMEnrichedRecommendation = Any  # type: ignore


def init_session_state(st) -> None:
    """Initialize session state keys if not present."""
    s = st.session_state
    if "place" not in s:
        s["place"] = None
    if "rating_label" not in s:
        s["rating_label"] = None
    if "price_label" not in s:
        s["price_label"] = None
    if "cuisine" not in s:
        s["cuisine"] = None
    if "recommendations" not in s:
        s["recommendations"] = []
    if "error_message" not in s:
        s["error_message"] = None
    if "loading" not in s:
        s["loading"] = False
    if "last_fetch_empty" not in s:
        s["last_fetch_empty"] = False


def set_recommendations(st, recs: List["LLMEnrichedRecommendation"]) -> None:
    """Store enriched recommendations and clear error."""
    s = st.session_state
    s["recommendations"] = recs
    s["error_message"] = None
    s["loading"] = False
    s["last_fetch_empty"] = len(recs) == 0


def set_error(st, message: str) -> None:
    """Store error and clear recommendations."""
    s = st.session_state
    s["error_message"] = message
    s["recommendations"] = []
    s["loading"] = False
    s["last_fetch_empty"] = False


def set_loading(st, value: bool) -> None:
    """Set loading indicator."""
    st.session_state["loading"] = value
