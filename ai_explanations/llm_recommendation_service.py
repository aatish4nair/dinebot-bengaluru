"""
ai_explanations – High-level API: enriched recommendations with LLM justifications.

Orchestrates recommender recommendations, builds prompt, calls Groq (Llama 3.1),
and returns LLMEnrichedRecommendation list with 2-line explanations.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# Ensure project root on path when this module is run or imported from ai_explanations
_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from recommender.recommendation_service import get_recommendations
from recommender.schemas import UserPreferences

from . import config as llm_config
from .groq_client import chat_completion
from .llm_formatter import build_messages, parse_justifications
from .schemas import LLMEnrichedRecommendation


def get_enriched_recommendations(
    preferences: UserPreferences,
    *,
    api_key: str | None = None,
    config: llm_config.LLMConfig | None = None,
) -> List[LLMEnrichedRecommendation]:
    """
    Get ranked restaurant recommendations with 2-line LLM justifications.

    Pipeline:
        1. Calls recommender get_recommendations(preferences) to retrieve candidate restaurants.
        2. If recommender returns restaurants, passes them to the LLM for enrichment.
        3. If recommender returns an empty list, returns that empty list directly.
        4. If the LLM call fails for any reason, falls back to returning the
           recommender recommendations with a generic explanation.

    Uses GROQ_API_KEY from the project root .env (or environment) unless api_key is passed.

    Returns:
        List of LLMEnrichedRecommendation (restaurant, score, explanation).
    """
    recommendations = get_recommendations(preferences)
    # If recommender returns no candidates, propagate that result directly.
    if not recommendations:
        return []

    cfg = config or llm_config.get_llm_config(api_key=api_key)
    if not cfg.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to the project root .env or set the environment variable."
        )

    try:
        messages = build_messages(preferences, recommendations)
        raw_response = chat_completion(
            messages,
            config=cfg,
            api_key=api_key,
        )
        explanations = parse_justifications(raw_response, recommendations)
    except Exception:
        # If the LLM step fails, fall back to recommender recommendations with a
        # generic explanation so that recommendations are still returned.
        return [
            LLMEnrichedRecommendation(
                restaurant=rec.restaurant,
                score=rec.score,
                explanation="Recommended for your preferences.",
            )
            for rec in recommendations
        ]

    return [
        LLMEnrichedRecommendation(
            restaurant=rec.restaurant,
            score=rec.score,
            explanation=explanations[i] if i < len(explanations) else "Recommended for your preferences.",
        )
        for i, rec in enumerate(recommendations)
    ]


if __name__ == "__main__":
    # Manual smoke test: requires features gold data and valid GROQ_API_KEY in the project root .env
    from recommender.schemas import UserPreferences

    prefs = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1000,
        cuisines=["North Indian", "Chinese"],
    )
    try:
        enriched = get_enriched_recommendations(prefs)
        print(f"Got {len(enriched)} enriched recommendations.")
        for e in enriched[:3]:
            print(f"- {e.restaurant.name}: {e.explanation[:80]}...")
    except Exception as exc:
        print(f"Error: {exc}")
