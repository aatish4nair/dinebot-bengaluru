"""
Phase 4 – Prompt templates for LLM-generated restaurant justifications.

Formats user preferences and restaurant list into a prompt that asks Llama 3.1
for exactly two lines per restaurant (price, ratings, cuisines).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# Ensure project root on path for Phase3 imports
_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase3.schemas import Recommendation, UserPreferences


def format_user_preferences(preferences: UserPreferences) -> str:
    """Format user preferences for inclusion in the prompt."""
    parts = []
    if preferences.place:
        parts.append(f"Place/Locality: {preferences.place}")
    if preferences.min_rating is not None:
        parts.append(f"Minimum rating: {preferences.min_rating}")
    if preferences.max_price_for_two is not None:
        parts.append(f"Maximum price for two: ₹{preferences.max_price_for_two}")
    if preferences.cuisines:
        parts.append(f"Preferred cuisines: {', '.join(preferences.cuisines)}")
    if not parts:
        return "No specific preferences (general recommendations)."
    return "\n".join(parts)


def format_restaurant_for_prompt(index: int, name: str, locality: str, rating: float | None, cost: float | None, cuisines: list[str]) -> str:
    """Format a single restaurant for the prompt."""
    rating_str = f"{rating:.1f}" if rating is not None else "N/A"
    cost_str = f"₹{cost}" if cost is not None else "N/A"
    cuisines_str = ", ".join(cuisines) if cuisines else "N/A"
    return f"{index}. {name} (Locality: {locality}, Rating: {rating_str}, Cost for two: {cost_str}, Cuisines: {cuisines_str})"


def build_restaurant_list(recommendations: list[Recommendation]) -> str:
    """Build the numbered list of restaurants for the prompt."""
    lines = []
    for i, rec in enumerate(recommendations, start=1):
        r = rec.restaurant
        lines.append(
            format_restaurant_for_prompt(
                i,
                r.name,
                r.locality,
                r.aggregate_rating,
                r.average_cost_for_two,
                r.cuisines,
            )
        )
    return "\n".join(lines)


SYSTEM_INSTRUCTION = """You are a helpful assistant that writes short, concise justifications for restaurant recommendations in Bengaluru.
For each restaurant listed, you must write exactly two lines. Focus on:
- Price suitability (whether it fits the user's budget).
- Ratings (how well it is rated).
- Cuisines (match to user preferences).

Keep each justification to exactly two short sentences. Do not add extra commentary before or after the list."""


def build_justification_prompt(preferences: UserPreferences, recommendations: list[Recommendation]) -> str:
    """
    Build the full user prompt asking for 2-line justifications per restaurant.

    Returns the user message content (not the full messages list).
    """
    prefs_block = format_user_preferences(preferences)
    restaurant_block = build_restaurant_list(recommendations)

    return f"""User preferences:
{prefs_block}

Recommended restaurants (numbered):
{restaurant_block}

For each restaurant above, write exactly two lines explaining why it is a good match. Use this exact format so we can parse your response:

Restaurant 1: [First line]. [Second line.]
Restaurant 2: [First line]. [Second line.]
... and so on for each number.

Write only the numbered lines (e.g. "Restaurant 1: ...", "Restaurant 2: ...") with no other text before or after."""
