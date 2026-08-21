"""
web – Adapter from UI form data to ai_explanations.get_enriched_recommendations.

Calls ai_explanations and returns a deduplicated list of recommendations.
GROQ_API_KEY is loaded from the project root .env in app initialization; retrieve with os.getenv.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ai_explanations.llm_recommendation_service import get_enriched_recommendations
from ai_explanations.schemas import LLMEnrichedRecommendation
from recommender.schemas import UserPreferences


def _ensure_groq_api_key() -> str | None:
    """Return GROQ_API_KEY from the environment if set."""
    return os.environ.get("GROQ_API_KEY")


def fetch_enriched_recommendations(preferences: UserPreferences) -> List[LLMEnrichedRecommendation]:
    """
    Call ai_explanations and return recommendations, deduplicated by restaurant name.
    Loads GROQ_API_KEY from the project root .env if not already in environment.
    """
    api_key = _ensure_groq_api_key()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to the project root .env (one line: GROQ_API_KEY=your_key)"
        )
    raw = get_enriched_recommendations(preferences, api_key=api_key)
    seen = set()
    out: List[LLMEnrichedRecommendation] = []
    for r in raw:
        name = (r.restaurant.name or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(r)
    return out
