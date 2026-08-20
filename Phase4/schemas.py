"""
Phase 4 – Data models for LLM-enriched recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass

# Import after Phase4/__init__.py has added project root to sys.path
from Phase3.schemas import RestaurantRecord


@dataclass
class LLMEnrichedRecommendation:
    """
    A restaurant recommendation with an LLM-generated 2-line explanation.
    """

    restaurant: RestaurantRecord
    score: float
    explanation: str  # Exactly 2 lines (price, ratings, cuisines)
